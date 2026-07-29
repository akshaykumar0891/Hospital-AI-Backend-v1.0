import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from database.excel_manager import ExcelManager
from services.availability_service import AvailabilityService

# Setup logging
logger = logging.getLogger(__name__)

class AppointmentService:
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
        """Normalizes mobile number by removing spaces, hyphens, and formatting."""
        if not mobile_str:
            return ""
        return re.sub(r"[\s\-\(\)\+]", "", str(mobile_str))

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Cancels an appointment by ID. Updates status to Cancelled and saves timestamp.
        """
        logger.info(f"Cancellation requested for Appointment ID: {appointment_id}")
        
        # 1. Find Appointment
        appt = self.db.get_appointment_by_id(appointment_id)
        if not appt:
            logger.warning(f"Cancellation failed: Appointment {appointment_id} not found")
            return {
                "success": False,
                "message": f"Appointment ID {appointment_id} not found."
            }

        # 2. Check current status
        status = str(appt.get("Status", "")).strip().lower()
        if status == "cancelled":
            logger.warning(f"Cancellation failed: Appointment {appointment_id} is already cancelled")
            return {
                "success": False,
                "message": "Appointment is already cancelled."
            }

        # 3. Update in database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates = {
            "Status": "Cancelled",
            "Cancelled At": timestamp
        }
        
        success = self.db.update_appointment(appointment_id, updates)
        if not success:
            logger.error(f"Failed to update Excel for cancelling appointment {appointment_id}")
            return {
                "success": False,
                "message": "Failed to cancel the appointment due to a database save error."
            }

        logger.info(f"Successfully cancelled appointment {appointment_id}")
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment cancelled successfully."
        }

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Dict[str, Any]:
        """
        Reschedules an existing appointment to a new date and time.
        """
        logger.info(f"Reschedule requested for Appointment ID {appointment_id} to {new_date} at {new_time}")

        # 1. Input format validations
        try:
            datetime.strptime(new_date.strip(), "%Y-%m-%d")
        except ValueError:
            return {"success": False, "message": f"Invalid date format: '{new_date}'. Use YYYY-MM-DD"}

        new_time_norm = self.normalize_time(new_time)
        try:
            parts = new_time_norm.split(":")
            if len(parts) < 2 or int(parts[0]) > 23 or int(parts[1]) > 59:
                raise ValueError
        except ValueError:
            return {"success": False, "message": f"Invalid time format: '{new_time}'. Use HH:MM"}

        # 2. Find Appointment
        appt = self.db.get_appointment_by_id(appointment_id)
        if not appt:
            logger.warning(f"Reschedule failed: Appointment {appointment_id} not found")
            return {
                "success": False,
                "message": f"Appointment ID {appointment_id} not found."
            }

        # 3. Check status
        status = str(appt.get("Status", "")).strip().lower()
        if status == "cancelled":
            logger.warning(f"Reschedule failed: Appointment {appointment_id} is cancelled")
            return {
                "success": False,
                "message": "Cannot reschedule a cancelled appointment."
            }

        # 4. Check if new slot matches current slot
        curr_date = str(appt.get("Date", "")).strip()
        curr_time = self.normalize_time(appt.get("Time", ""))
        if curr_date == new_date.strip() and curr_time == new_time_norm:
            logger.info("Reschedule requested for the same date and time slot")
            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": "Appointment is already scheduled at this date and time."
            }

        # 5. Check slot availability for the doctor
        doctor_id = appt.get("Doctor ID")
        avail_res = self.avail.get_available_slots(doctor_id, new_date)
        if avail_res.get("status") == "error":
            return {"success": False, "message": avail_res.get("message")}

        available_slots = avail_res.get("available_slots", [])
        if new_time_norm not in available_slots:
            logger.warning(f"Reschedule failed: Slot {new_time_norm} is unavailable for doctor {doctor_id} on {new_date}")
            return {
                "success": False,
                "message": f"Selected time slot {new_time_norm} is unavailable.",
                "available_slots": available_slots,
                "next_available_date": avail_res.get("next_available_date")
            }

        # 6. Update database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates = {
            "Date": new_date,
            "Time": new_time_norm,
            "Status": "Rescheduled",
            "Updated At": timestamp
        }

        success = self.db.update_appointment(appointment_id, updates)
        if not success:
            logger.error(f"Failed to update Excel for rescheduling appointment {appointment_id}")
            return {
                "success": False,
                "message": "Failed to reschedule the appointment due to a database save error."
            }

        logger.info(f"Successfully rescheduled appointment {appointment_id} to {new_date} {new_time_norm}")
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment rescheduled successfully."
        }

    def get_appointment_status(self, appointment_id: Optional[str] = None, mobile: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves appointment status by Appointment ID or Mobile Number.
        """
        if not appointment_id and not mobile:
            return {"success": False, "message": "Must provide either appointment_id or mobile number."}

        # Lookup by ID
        if appointment_id:
            appt = self.db.get_appointment_by_id(appointment_id)
            if appt:
                return {
                    "success": True,
                    "appointments": [appt]
                }
            else:
                return {
                    "success": False,
                    "message": f"No appointment found with ID: {appointment_id}"
                }

        # Lookup by mobile
        if mobile:
            search_mobile = self.normalize_mobile(mobile)
            all_appts = self.db.get_appointments()
            matching = []
            for appt in all_appts:
                appt_mobile = self.normalize_mobile(appt.get("Mobile", ""))
                if appt_mobile == search_mobile:
                    matching.append(appt)
            
            if matching:
                # Sort matching appointments by Date and Time (active first, or reverse chronological)
                matching.sort(key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True)
                return {
                    "success": True,
                    "appointments": matching
                }
            else:
                return {
                    "success": False,
                    "message": f"No appointments found matching the mobile number: {mobile}"
                }

