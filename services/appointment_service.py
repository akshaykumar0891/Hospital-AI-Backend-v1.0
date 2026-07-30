import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Appointment
from services.availability_service import AvailabilityService

# Setup logging
logger = logging.getLogger(__name__)

class AppointmentService:
    def __init__(self, db: Session, availability_service: Optional[AvailabilityService] = None):
        self.db = db
        self.avail = availability_service or AvailabilityService(db)

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

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Soft-deletes an appointment by setting its status to 'Cancelled' and setting
        the cancellation timestamp.
        """
        logger.info(f"Cancellation requested for Appointment ID: {appointment_id}")

        appt = self.db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
        if not appt:
            logger.warning(f"Appointment ID {appointment_id} not found.")
            return {
                "success": False,
                "message": f"Appointment ID {appointment_id} not found."
            }

        if appt.status == "Cancelled":
            logger.warning(f"Appointment ID {appointment_id} is already cancelled.")
            return {
                "success": False,
                "message": "Appointment is already cancelled."
            }

        # Update appointment status in database
        appt.status = "Cancelled"
        appt.cancelled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.commit()

        logger.info(f"Successfully cancelled appointment {appointment_id}")
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment cancelled successfully."
        }

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Dict[str, Any]:
        """
        Updates target appointment's Date and Time, sets its status to 'Rescheduled',
        and runs availability validation checks.
        """
        logger.info(f"Reschedule requested for Appointment ID {appointment_id} to {new_date} at {new_time}")

        appt = self.db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
        if not appt:
            logger.warning(f"Appointment ID {appointment_id} not found.")
            return {
                "success": False,
                "message": f"Appointment ID {appointment_id} not found."
            }

        if appt.status == "Cancelled":
            logger.warning(f"Reschedule failed: Appointment {appointment_id} is already cancelled.")
            return {
                "success": False,
                "message": "Cannot reschedule a cancelled appointment."
            }

        doctor_id = appt.doctor_id
        doctor_name = appt.doctor_name
        current_date = appt.appointment_date
        current_time = self.normalize_time(appt.appointment_time)
        new_time_norm = self.normalize_time(new_time)

        # Date format validation
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "message": f"Invalid date format: '{new_date}'. Use YYYY-MM-DD"}

        # Time format validation
        try:
            parts = new_time.split(":")
            if len(parts) < 2:
                raise ValueError
            int(parts[0])
            int(parts[1])
        except ValueError:
            return {"success": False, "message": f"Invalid time format: '{new_time}'. Use HH:MM"}

        # If date and time are identical, return success with no action
        if current_date == new_date and current_time == new_time_norm:
            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": "Appointment rescheduled successfully."
            }

        # Validate availability using AvailabilityService
        avail_res = self.avail.get_available_slots(doctor_id, new_date)
        if avail_res.get("status") == "error":
            return {"success": False, "message": avail_res.get("message")}

        available_slots = avail_res.get("available_slots", [])
        if new_time_norm not in available_slots:
            logger.warning(f"Reschedule failed: Slot {new_time_norm} is unavailable for {doctor_name} on {new_date}")
            return {
                "success": False,
                "message": f"Selected time slot {new_time_norm} is unavailable.",
                "available_slots": available_slots,
                "next_available_date": avail_res.get("next_available_date")
            }

        # Update reschedule coordinates in database
        appt.appointment_date = new_date
        appt.appointment_time = new_time_norm
        appt.status = "Rescheduled"
        appt.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.commit()

        logger.info(f"Successfully rescheduled appointment {appointment_id} to {new_date} {new_time_norm}")
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment rescheduled successfully."
        }

    def get_appointment_status(self, appointment_id: Optional[str] = None, mobile: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves appointment matching either specific ID or specific mobile,
        formatting response back to original list formats.
        """
        if not appointment_id and not mobile:
            return {
                "success": False,
                "message": "Provide either appointment_id or mobile query parameter."
            }

        query = self.db.query(Appointment)
        if appointment_id:
            query = query.filter(Appointment.appointment_id == appointment_id)
        if mobile:
            mobile_cleaned = self.normalize_mobile(mobile)
            query = query.filter(Appointment.mobile == mobile_cleaned)

        appts = query.all()
        mapped_appts = []
        for appt in appts:
            mapped_appts.append({
                "Appointment ID": appt.appointment_id,
                "Patient Name": appt.patient_name,
                "Mobile": int(appt.mobile) if appt.mobile.isdigit() else appt.mobile,
                "Doctor ID": appt.doctor_id,
                "Doctor Name": appt.doctor_name,
                "Department": appt.department,
                "Date": appt.appointment_date,
                "Time": appt.appointment_time,
                "Status": appt.status,
                "Created At": appt.created_at,
                "Updated At": appt.updated_at,
                "Cancelled At": appt.cancelled_at
            })

        # Return format matching route specifications
        # Wait, if no appointments are found, did the old one return an error?
        # In Excel version, if appointment_id was provided and not found, it returned success=False.
        # If mobile was provided and not found, it returned success=False.
        # Wait! Let's check how the previous route handled empty matches.
        # Let's check routes/booking_routes.py's implementation of `/appointment-status`!
        # Actually, the route itself delegates directly to the service:
        # return service.get_appointment_status(appointment_id, mobile)
        # In our previous Excel version:
        # If no appointment ID was found, it returned:
        # {"success": False, "message": f"No appointment found with ID: {appointment_id}"}
        # If no mobile was found, it returned:
        # {"success": False, "message": f"No appointments found matching the mobile number: {mobile}"}
        # Let's replicate this exact error behavior to be 100% compatible!
        if not mapped_appts:
            if appointment_id:
                return {
                    "success": False,
                    "message": f"No appointment found with ID: {appointment_id}"
                }
            else:
                return {
                    "success": False,
                    "message": f"No appointments found matching the mobile number: {mobile}"
                }

        # If it found appointments, sort them by Date and Time (active first, or reverse chronological)
        # to match exact previous sort behavior!
        mapped_appts.sort(key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True)

        return {
            "success": True,
            "appointments": mapped_appts
        }

