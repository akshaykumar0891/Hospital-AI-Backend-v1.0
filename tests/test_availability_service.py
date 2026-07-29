import sys
import os
import shutil
from pathlib import Path
from datetime import date, datetime

# Add project root to path
sys.path.append("d:/hospital-ai")

from database.excel_manager import ExcelManager
from services.availability_service import AvailabilityService
from config import EXCEL_DB_PATH

def test_availability_service():
    original_db = EXCEL_DB_PATH
    test_db = original_db.parent / "hospital_data_test_avail.xlsx"

    print(f"Original DB Path: {original_db}")
    print(f"Test DB Path: {test_db}")

    shutil.copy2(original_db, test_db)
    print("Copied database to test database file.")

    try:
        manager = ExcelManager(file_path=str(test_db))
        service = AvailabilityService(excel_manager=manager)

        # 1. Test Day parsing
        mon_sat = service.parse_available_days("Mon-Sat")
        print("\nParsed 'Mon-Sat' days:", mon_sat)
        assert mon_sat == [0, 1, 2, 3, 4, 5]

        mon_wed_fri = service.parse_available_days("Mon,Tue,Wed,Fri")
        print("Parsed 'Mon,Tue,Wed,Fri' days:", mon_wed_fri)
        assert mon_wed_fri == [0, 1, 2, 4]
        print("Day parsing tests passed.")

        # 2. Test Time Slot generation
        slots = service.generate_slots("09:00", "11:00", 30)
        print("\nGenerated slots (09:00 - 11:00, 30m):", slots)
        assert slots == ["09:00", "09:30", "10:00", "10:30"]
        print("Slot generation tests passed.")

        # 3. Test Availability Check on a day the doctor is NOT working
        # Rajesh Kumar (D001) works Mon,Tue,Wed,Fri (0, 1, 2, 4).
        # Let's check 2026-08-01 (Saturday, weekday = 5). He does not work Saturdays.
        check_date_str = "2026-08-01"  # Saturday
        res = service.get_available_slots("D001", check_date_str)
        print("\nAvailability check on Saturday (non-working day) for D001:")
        print(res)
        assert res["status"] == "unavailable"
        # Next working day should be Monday (2026-08-03)
        assert res["next_available_date"] == "2026-08-03"
        print("Doctor non-working day check passed.")

        # 4. Test Availability Check on a working day with no bookings
        # check on 2026-08-03 (Monday). No bookings yet.
        res_mon = service.get_available_slots("D001", "2026-08-03")
        print("\nAvailability check on Monday for D001 (no bookings):")
        print(res_mon)
        assert res_mon["status"] == "available"
        assert len(res_mon["available_slots"]) == 8 # 09:00 to 13:00 is 8 slots
        assert all(s["available"] is True for s in res_mon["slots"])
        print("Doctor working day (no bookings) check passed.")

        # 5. Save a booked appointment and verify it shows as booked (False)
        test_appt = {
            "Appointment ID": "APP-AVAIL-TEST-001",
            "Patient Name": "Bob Builder",
            "Mobile": "5555555555",
            "Doctor ID": "D001",
            "Doctor Name": "Dr. Rajesh Kumar",
            "Department": "Cardiology",
            "Date": "2026-08-03",
            "Time": "10:00",
            "Status": "Booked"
        }
        manager.save_appointment(test_appt)
        print("\nSaved a booked appointment for 2026-08-03 10:00.")

        res_mon_booked = service.get_available_slots("D001", "2026-08-03")
        print("\nAvailability check on Monday for D001 (with 1 booking):")
        print(res_mon_booked)
        assert res_mon_booked["status"] == "available"
        assert "10:00" not in res_mon_booked["available_slots"]
        # Find 10:00 slot in the full list and assert it is unavailable
        slot_10 = next(s for s in res_mon_booked["slots"] if s["time"] == "10:00")
        assert slot_10["available"] is False
        print("Booked slot verification passed.")

        # 6. Test fully booked date alternative search
        # D001 has 8 slots. Let's book the remaining 7 slots to make him fully booked!
        slots_to_book = ["09:00", "09:30", "10:30", "11:00", "11:30", "12:00", "12:30"]
        for idx, t in enumerate(slots_to_book):
            manager.save_appointment({
                "Appointment ID": f"APP-AVAIL-TEST-FB-{idx}",
                "Patient Name": f"Patient {idx}",
                "Mobile": "5555555555",
                "Doctor ID": "D001",
                "Doctor Name": "Dr. Rajesh Kumar",
                "Department": "Cardiology",
                "Date": "2026-08-03",
                "Time": t,
                "Status": "Booked"
            })
        print(f"\nBooked remaining slots: {slots_to_book}.")

        res_mon_fb = service.get_available_slots("D001", "2026-08-03")
        print("\nAvailability check on Monday for D001 (fully booked):")
        print(res_mon_fb)
        assert res_mon_fb["status"] == "fully_booked"
        # Next working day should be Tuesday (2026-08-04)
        assert res_mon_fb["next_available_date"] == "2026-08-04"
        print("Fully booked date check passed.")

        print("\nAll AvailabilityService tests passed successfully!")

    finally:
        if os.path.exists(test_db):
            os.remove(test_db)
            print("\nRemoved test database file.")

if __name__ == "__main__":
    test_availability_service()
