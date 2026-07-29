import sys
import shutil
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app
from config import EXCEL_DB_PATH

def test_fastapi_endpoints():
    original_db = EXCEL_DB_PATH
    test_db = original_db.parent / "hospital_data_test_api.xlsx"

    print(f"Original DB Path: {original_db}")
    print(f"Test DB Path: {test_db}")

    shutil.copy2(original_db, test_db)
    print("Copied database to test database file.")

    # Override dependencies
    from database.excel_manager import ExcelManager
    from routes.doctor_routes import get_excel_manager as doc_get_db
    from routes.booking_routes import get_excel_manager as book_get_db

    test_manager = ExcelManager(file_path=str(test_db))
    app.dependency_overrides[doc_get_db] = lambda: test_manager
    app.dependency_overrides[book_get_db] = lambda: test_manager

    client = TestClient(app)

    try:
        # 1. Test /health
        print("\n--- 1. Testing GET /health ---")
        res = client.get("/health")
        print("Health status response:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["status"] == "healthy"

        # 2. Test /api/v1/doctors
        print("\n--- 2. Testing GET /api/v1/doctors ---")
        res = client.get("/api/v1/doctors")
        print("Doctors list count:", len(res.json()["data"]))
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert len(res.json()["data"]) == 3

        # 3. Test /api/v1/hospital-info
        print("\n--- 3. Testing GET /api/v1/hospital-info ---")
        res = client.get("/api/v1/hospital-info")
        print("Hospital info response:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["Hospital Name"] == "ABC Hospital"

        # 3b. Test /api/v1/system-info
        print("\n--- 3b. Testing GET /api/v1/system-info ---")
        res = client.get("/api/v1/system-info")
        print("System info response:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["service"] == "Hospital AI Backend"
        assert res.json()["data"]["environment"] == "development"

        # 4. Test /api/v1/check-availability
        print("\n--- 4. Testing POST /api/v1/check-availability ---")
        avail_payload = {"doctor_id": "D001", "date": "2026-08-03"}
        res = client.post("/api/v1/check-availability", json=avail_payload)
        print("Availability result:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert len(res.json()["data"]["available_slots"]) == 8

        # 5. Test /api/v1/book-appointment
        print("\n--- 5. Testing POST /api/v1/book-appointment ---")
        book_payload = {
            "patient_name": "David",
            "mobile": "9998887776",
            "doctor_name": "Dr. Rajesh Kumar",
            "date": "2026-08-03",
            "time": "10:30"
        }
        res = client.post("/api/v1/book-appointment", json=book_payload)
        print("Book result:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        appt_id = res.json()["data"]["appointment_id"]
        assert appt_id.startswith("APT-")

        # Duplicate check
        res_dup = client.post("/api/v1/book-appointment", json=book_payload)
        print("Duplicate book result:", res_dup.json())
        assert res_dup.status_code == 200
        assert res_dup.json()["success"] is False
        assert "already exists" in res_dup.json()["message"]

        # Booked slot check (different patient)
        book_payload_diff = book_payload.copy()
        book_payload_diff["patient_name"] = "Gary"
        book_payload_diff["mobile"] = "1111111111"
        res_diff = client.post("/api/v1/book-appointment", json=book_payload_diff)
        print("Booked slot result:", res_diff.json())
        assert res_diff.status_code == 200
        assert res_diff.json()["success"] is False
        assert "10:30" not in res_diff.json()["data"]["available_slots"]

        # 6. Test /api/v1/appointment-status
        print("\n--- 6. Testing GET /api/v1/appointment-status ---")
        res = client.get(f"/api/v1/appointment-status?appointment_id={appt_id}")
        print("Status by ID result:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["appointments"][0]["Patient Name"] == "David"

        res_mob = client.get("/api/v1/appointment-status?mobile=9998887776")
        print("Status by Mobile result:", res_mob.json())
        assert res_mob.status_code == 200
        assert res_mob.json()["success"] is True
        assert len(res_mob.json()["data"]["appointments"]) == 1

        # 7. Test /api/v1/reschedule-appointment
        print("\n--- 7. Testing POST /api/v1/reschedule-appointment ---")
        resched_payload = {
            "appointment_id": appt_id,
            "new_date": "2026-08-03",
            "new_time": "12:00"
        }
        res = client.post("/api/v1/reschedule-appointment", json=resched_payload)
        print("Reschedule result:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Verify updated date/time in status lookup
        res_check = client.get(f"/api/v1/appointment-status?appointment_id={appt_id}")
        appt_detail = res_check.json()["data"]["appointments"][0]
        assert appt_detail["Time"] == "12:00"
        assert appt_detail["Status"] == "Rescheduled"
        assert appt_detail["Updated At"] is not None

        # 8. Test /api/v1/cancel-appointment
        print("\n--- 8. Testing POST /api/v1/cancel-appointment ---")
        cancel_payload = {"appointment_id": appt_id}
        res = client.post("/api/v1/cancel-appointment", json=cancel_payload)
        print("Cancel result:", res.json())
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Verify updated status to Cancelled
        res_check_cancel = client.get(f"/api/v1/appointment-status?appointment_id={appt_id}")
        appt_detail_cancel = res_check_cancel.json()["data"]["appointments"][0]
        assert appt_detail_cancel["Status"] == "Cancelled"
        assert appt_detail_cancel["Cancelled At"] is not None

        print("\nAll FastAPI Router endpoints tests passed successfully!")

    finally:
        # Clear overrides and clean up
        app.dependency_overrides.clear()
        if os.path.exists(test_db):
            os.remove(test_db)
            print("\nRemoved test database file.")

if __name__ == "__main__":
    test_fastapi_endpoints()
