import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from database.excel_manager import ExcelManager
from services.availability_service import AvailabilityService
from utils.id_generator import generate_appointment_id

# Setup logging
logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self, excel_manager: Optional[ExcelManager] = None, availability_service: Optional[AvailabilityService] = None):
        self.db = excel_manager or ExcelManager()
        self.avail = availability_service or AvailabilityService(self.db)

    def normalize_time(self, time_str: str) -> str:
        """Normalizes time to HH:MM format."""
        if not time_str:
            return ""
        parts = str(time_str).split(":")
        if len(parts) >= 2:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
        return time_str

    def normalize_mobile(self, mobile_str: str) -> str:
        """Removes spaces, hyphens, and parentheses from mobile numbers."""
        if not mobile_str:
            return ""
        return re.sub(r"[\s\-\(\)\+]", "", str(mobile_str))

    def validate_booking_inputs(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validates the inputs for creating a booking.
        Returns a dict with error message if invalid, or None if valid.
        """
        required_fields = ["patient_name", "mobile", "doctor_name", "date", "time"]
        for field in required_fields:
            if not data.get(field):
                return {"success": False, "message": f"Missing required field: {field}"}

        # Date format validation YYYY-MM-DD
        date_str = str(data["date"]).strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "message": f"Invalid date format: '{date_str}'. Use YYYY-MM-DD"}

        # Time format validation HH:MM (allow seconds and normalize)
        time_str = str(data["time"]).strip()
        try:
            parts = time_str.split(":")
            if len(parts) < 2:
                raise ValueError
            int(parts[0])
            int(parts[1])
        except ValueError:
            return {"success": False, "message": f"Invalid time format: '{time_str}'. Use HH:MM"}

        # Mobile validation (must contain digits)
        mobile_cleaned = self.normalize_mobile(data["mobile"])
        if not mobile_cleaned.isdigit() or len(mobile_cleaned) < 5:
            return {"success": False, "message": f"Invalid mobile number: '{data['mobile']}'"}

        return None

    def book_appointment(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates, checks availability, and books an appointment.
        """
        logger.info(f"Received booking request for patient: {booking_data.get('patient_name')}")

        # 1. Input Validation
        validation_error = self.validate_booking_inputs(booking_data)
        if validation_error:
            logger.warning(f"Booking validation failed: {validation_error['message']}")
            return validation_error

        patient_name = str(booking_data["patient_name"]).strip()
        mobile = self.normalize_mobile(booking_data["mobile"])
        doctor_name_input = str(booking_data["doctor_name"]).strip()
        date_str = str(booking_data["date"]).strip()
        time_str = self.normalize_time(booking_data["time"])

        # 2. Verify Doctor Exists
        doctor = self.db.get_doctor_by_name(doctor_name_input)
        if not doctor:
            logger.warning(f"Doctor '{doctor_name_input}' not found")
            return {"success": False, "message": f"Doctor '{doctor_name_input}' not found"}

        doctor_id = doctor["Doctor ID"]
        doctor_name = doctor["Doctor Name"]
        department = doctor["Department"]

        # 3. Check for Duplicate Active Booking
        # Same doctor, same date, same time, and same patient mobile
        existing_appointments = self.db.get_appointments()
        for appt in existing_appointments:
            appt_doc_id = str(appt.get("Doctor ID", "")).strip().lower()
            appt_date = str(appt.get("Date", "")).strip()
            appt_time = self.normalize_time(appt.get("Time", ""))
            appt_mobile = self.normalize_mobile(appt.get("Mobile", ""))
            appt_status = str(appt.get("Status", "")).strip().lower()

            if (appt_doc_id == doctor_id.lower() and 
                appt_date == date_str and 
                appt_time == time_str and 
                appt_mobile == mobile and 
                appt_status != "cancelled"):
                
                logger.warning(f"Duplicate booking attempt detected for mobile {mobile}")
                return {
                    "success": False,
                    "message": "An appointment already exists for this patient at the selected time."
                }

        # 4. Check Availability via AvailabilityService
        avail_res = self.avail.get_available_slots(doctor_id, date_str)
        if avail_res.get("status") == "error":
            return {"success": False, "message": avail_res.get("message")}

        # Check if the requested slot is available
        available_slots = avail_res.get("available_slots", [])
        if time_str not in available_slots:
            logger.warning(f"Slot {time_str} is not available for doctor {doctor_name} on {date_str}")
            return {
                "success": False,
                "message": f"Selected time slot {time_str} is unavailable.",
                "available_slots": available_slots,
                "next_available_date": avail_res.get("next_available_date")
            }

        # 5. Generate Professional Sequential ID
        existing_ids = [appt.get("Appointment ID") for appt in existing_appointments if appt.get("Appointment ID")]
        appt_id = generate_appointment_id(existing_ids)

        # 6. Save the Appointment
        appointment_payload = {
            "Appointment ID": appt_id,
            "Patient Name": patient_name,
            "Mobile": mobile,
            "Doctor ID": doctor_id,
            "Doctor Name": doctor_name,
            "Department": department,
            "Date": date_str,
            "Time": time_str,
            "Status": "Booked"
        }
        self.db.save_appointment(appointment_payload)

        logger.info(f"Successfully booked appointment {appt_id} for {patient_name}")
        return {
            "success": True,
            "appointment_id": appt_id,
            "message": "Appointment booked successfully."
        }

