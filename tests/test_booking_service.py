import sys
import os
import shutil
from pathlib import Path

# Add project root to path
sys.path.append("d:/hospital-ai")

from database.excel_manager import ExcelManager
from services.availability_service import AvailabilityService
from services.booking_service import BookingService
from config import EXCEL_DB_PATH

def test_booking_service():
    original_db = EXCEL_DB_PATH
    test_db = original_db.parent / "hospital_data_test_booking.xlsx"

    print(f"Original DB Path: {original_db}")
    print(f"Test DB Path: {test_db}")

    shutil.copy2(original_db, test_db)
    print("Copied database to test database file.")

    try:
        manager = ExcelManager(file_path=str(test_db))
        avail_service = AvailabilityService(excel_manager=manager)
        booking_service = BookingService(excel_manager=manager, availability_service=avail_service)

        # 1. Test Input Validation Failures
        print("\n--- 1. Testing Validation Failures ---")
        # Missing field
        bad_req1 = {"patient_name": "", "mobile": "123456", "doctor_name": "Dr. Rajesh Kumar", "date": "2026-08-03", "time": "09:00"}
        res = booking_service.book_appointment(bad_req1)
        print("Missing field result:", res)
        assert res["success"] is False
        assert "Missing required field" in res["message"]

        # Invalid Date format
        bad_req2 = {"patient_name": "Akshay", "mobile": "9876543210", "doctor_name": "Dr. Rajesh Kumar", "date": "08-03-2026", "time": "09:00"}
        res = booking_service.book_appointment(bad_req2)
        print("Bad Date format result:", res)
        assert res["success"] is False
        assert "Invalid date format" in res["message"]

        # Non-existent doctor
        bad_req3 = {"patient_name": "Akshay", "mobile": "9876543210", "doctor_name": "Dr. Strange", "date": "2026-08-03", "time": "09:00"}
        res = booking_service.book_appointment(bad_req3)
        print("Non-existent doctor result:", res)
        assert res["success"] is False
        assert "not found" in res["message"]

        # 2. Test Successful Booking
        print("\n--- 2. Testing Successful Booking ---")
        req1 = {
            "patient_name": "Akshay",
            "mobile": "9876543210",
            "doctor_name": "Dr. Rajesh Kumar",
            "date": "2026-08-03",  # Monday
            "time": "09:00"
        }
        res1 = booking_service.book_appointment(req1)
        print("Booking 1 result:", res1)
        assert res1["success"] is True
        assert res1["appointment_id"].startswith("APT-")
        first_appt_id = res1["appointment_id"]

        # Verify it got saved in database
        saved_appt = manager.get_appointment_by_id(first_appt_id)
        print("Saved appointment in Excel:", saved_appt)
        assert saved_appt is not None
        assert saved_appt["Patient Name"] == "Akshay"
        assert saved_appt["Department"] == "Cardiology"
        assert saved_appt["Created At"] is not None

        # 3. Test Duplicate Booking Block
        print("\n--- 3. Testing Duplicate Booking ---")
        res_dup = booking_service.book_appointment(req1)
        print("Duplicate booking result:", res_dup)
        assert res_dup["success"] is False
        assert "already exists" in res_dup["message"]

        # 4. Test Slot Already Booked (Different Patient)
        print("\n--- 4. Testing Slot Already Booked (Different Patient) ---")
        req2 = {
            "patient_name": "Suresh",
            "mobile": "8888888888",
            "doctor_name": "Dr. Rajesh Kumar",
            "date": "2026-08-03",
            "time": "09:00" # same slot
        }
        res2 = booking_service.book_appointment(req2)
        print("Slot booked by other result:", res2)
        assert res2["success"] is False
        assert "unavailable" in res2["message"]
        # Should return alternative slots
        assert "09:30" in res2["available_slots"]
        assert "09:00" not in res2["available_slots"]

        # 5. Test booking sequence increments
        print("\n--- 5. Testing Booking Sequence Increments ---")
        req3 = {
            "patient_name": "Suresh",
            "mobile": "8888888888",
            "doctor_name": "Dr. Rajesh Kumar",
            "date": "2026-08-03",
            "time": "09:30" # next slot
        }
        res3 = booking_service.book_appointment(req3)
        print("Booking 2 result:", res3)
        assert res3["success"] is True
        assert res3["appointment_id"] != first_appt_id
        # Extract numeric suffixes to verify increment
        num1 = int(first_appt_id.split("-")[1])
        num2 = int(res3["appointment_id"].split("-")[1])
        assert num2 == num1 + 1
        print(f"Generated sequential IDs: {first_appt_id} -> {res3['appointment_id']}")

        print("\nAll BookingService integration tests passed successfully!")

    finally:
        if os.path.exists(test_db):
            os.remove(test_db)
            print("\nRemoved test database file.")

if __name__ == "__main__":
    test_booking_service()
