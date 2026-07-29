import sys
import os
import shutil
from pathlib import Path

# Add project root to path
sys.path.append("d:/hospital-ai")

from database.excel_manager import ExcelManager
from config import EXCEL_DB_PATH

def test_excel_manager_enhanced():
    original_db = EXCEL_DB_PATH
    test_db = original_db.parent / "hospital_data_test_enhanced.xlsx"

    print(f"Original DB Path: {original_db}")
    print(f"Test DB Path: {test_db}")

    shutil.copy2(original_db, test_db)
    print("Copied database to test database file.")

    try:
        manager = ExcelManager(file_path=str(test_db))

        # 1. Test get_doctor_by_id
        doc1 = manager.get_doctor_by_id("D001")
        print("\n--- Doctor by ID (D001) ---")
        print(doc1)
        assert doc1 is not None
        assert doc1["Doctor Name"] == "Dr. Rajesh Kumar"
        print("get_doctor_by_id test passed.")

        # 2. Test get_doctor_by_name
        doc_name_exact = manager.get_doctor_by_name("Dr. Priya Sharma")
        print("\n--- Doctor by Name Exact (Dr. Priya Sharma) ---")
        print(doc_name_exact)
        assert doc_name_exact is not None
        assert doc_name_exact["Doctor ID"] == "D002"

        doc_name_norm = manager.get_doctor_by_name("priya sharma")
        print("\n--- Doctor by Name Normalized (priya sharma) ---")
        print(doc_name_norm)
        assert doc_name_norm is not None
        assert doc_name_norm["Doctor ID"] == "D002"
        print("get_doctor_by_name tests passed.")

        # 3. Save appointment with extra fields (Department, Created At)
        test_appt = {
            "Appointment ID": "APP-ENHANCED-001",
            "Patient Name": "Alice Smith",
            "Mobile": "9999999999",
            "Doctor ID": "D003",
            "Doctor Name": "Dr. Arjun Reddy",
            "Department": "General Medicine",
            "Date": "2026-08-05",
            "Time": "11:30",
            "Status": "Booked"
        }
        manager.save_appointment(test_appt)
        print("\nSaved enhanced test appointment.")

        # 4. Get appointment by ID
        saved_appt = manager.get_appointment_by_id("APP-ENHANCED-001")
        print("\n--- Saved Appointment by ID ---")
        print(saved_appt)
        assert saved_appt is not None
        assert saved_appt["Patient Name"] == "Alice Smith"
        assert saved_appt["Department"] == "General Medicine"
        assert saved_appt["Created At"] is not None
        print("save_appointment and get_appointment_by_id tests passed.")

        # 5. Delete appointment
        delete_success = manager.delete_appointment("APP-ENHANCED-001")
        print(f"\nDelete status: {delete_success}")
        assert delete_success is True

        # 6. Verify deleted
        deleted_appt = manager.get_appointment_by_id("APP-ENHANCED-001")
        assert deleted_appt is None, "Appointment was not deleted!"
        print("delete_appointment test passed.")

        print("\nAll enhanced ExcelManager tests passed successfully!")

    finally:
        if os.path.exists(test_db):
            os.remove(test_db)
            print("\nRemoved test database file.")

if __name__ == "__main__":
    test_excel_manager_enhanced()
