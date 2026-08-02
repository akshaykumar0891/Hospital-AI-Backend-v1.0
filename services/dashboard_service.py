import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database.models import Doctor, Appointment
from config import TIMEZONE

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> Dict[str, int]:
        """
        Calculates metric statistics for the admin dashboard panel dashboard.
        """
        tz = ZoneInfo(TIMEZONE)
        today_str = datetime.now(tz).strftime("%Y-%m-%d")

        try:
            # 1. Today's Appointments (status is not Cancelled and date is today)
            today_count = self.db.query(Appointment).filter(
                Appointment.appointment_date == today_str,
                Appointment.status != "Cancelled"
            ).count()

            # 2. Upcoming Appointments (status is not Cancelled and date is in the future)
            upcoming_count = self.db.query(Appointment).filter(
                Appointment.appointment_date > today_str,
                Appointment.status != "Cancelled"
            ).count()

            # 3. Cancelled Appointments (status is Cancelled)
            cancelled_count = self.db.query(Appointment).filter(
                Appointment.status == "Cancelled"
            ).count()

            # 4. Completed Appointments (status is Completed, or active and date is in the past)
            completed_count = self.db.query(Appointment).filter(
                or_(
                    Appointment.status == "Completed",
                    (Appointment.status != "Cancelled") & (Appointment.appointment_date < today_str)
                )
            ).count()

            # 5. Total Doctors
            total_doctors = self.db.query(Doctor).count()

            logger.info(f"Dashboard stats calculated: today={today_count}, upcoming={upcoming_count}, cancelled={cancelled_count}, completed={completed_count}, doctors={total_doctors}")

            return {
                "today_appointments": today_count,
                "upcoming_appointments": upcoming_count,
                "cancelled_appointments": cancelled_count,
                "completed_appointments": completed_count,
                "total_doctors": total_doctors
            }
        except Exception as e:
            logger.error(f"Error computing dashboard stats: {e}", exc_info=True)
            raise e

    def get_paginated_appointments(
        self, 
        page: int = 1, 
        limit: int = 10, 
        status: Optional[str] = None, 
        doctor_id: Optional[str] = None, 
        date: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves paginated, filtered, and sorted appointments list.
        """
        try:
            query = self.db.query(Appointment)

            # Apply Filters
            if status:
                query = query.filter(Appointment.status == status)
            if doctor_id:
                query = query.filter(Appointment.doctor_id == doctor_id)
            if date:
                query = query.filter(Appointment.appointment_date == date)
            if search:
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Appointment.patient_name.ilike(search_term),
                        Appointment.mobile.ilike(search_term),
                        Appointment.appointment_id.ilike(search_term)
                    )
                )

            # Calculate total match count
            total = query.count()

            # Order by date desc, time desc, created_at desc (newest first)
            query = query.order_by(
                Appointment.appointment_date.desc(),
                Appointment.appointment_time.desc(),
                Appointment.created_at.desc()
            )

            # Apply pagination offset limits
            offset = (page - 1) * limit
            appointments = query.offset(offset).limit(limit).all()

            # Map to response shape
            mapped_appointments = []
            for appt in appointments:
                mapped_appointments.append({
                    "appointment_id": appt.appointment_id,
                    "patient_name": appt.patient_name,
                    "mobile": int(appt.mobile) if appt.mobile.isdigit() else appt.mobile,
                    "doctor_name": appt.doctor_name,
                    "department": appt.department,
                    "appointment_date": appt.appointment_date,
                    "appointment_time": appt.appointment_time,
                    "status": appt.status,
                    "created_at": appt.created_at
                })

            total_pages = (total + limit - 1) // limit if total > 0 else 0

            return {
                "appointments": mapped_appointments,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
        except Exception as e:
            logger.error(f"Error querying paginated appointments: {e}", exc_info=True)
            raise e

    def get_appointment_detail(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the complete data fields for a single appointment model.
        """
        appt = self.db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
        if not appt:
            return None
        return {
            "appointment_id": appt.appointment_id,
            "patient_name": appt.patient_name,
            "mobile": int(appt.mobile) if appt.mobile.isdigit() else appt.mobile,
            "doctor_id": appt.doctor_id,
            "doctor_name": appt.doctor_name,
            "department": appt.department,
            "appointment_date": appt.appointment_date,
            "appointment_time": appt.appointment_time,
            "status": appt.status,
            "created_at": appt.created_at,
            "updated_at": appt.updated_at,
            "cancelled_at": appt.cancelled_at
        }

    def get_doctors(self) -> List[Dict[str, Any]]:
        """
        Returns the doctors directory schedules.
        """
        docs = self.db.query(Doctor).all()
        return [{
            "doctor_id": doc.doctor_id,
            "doctor_name": doc.doctor_name,
            "department": doc.department,
            "available_days": doc.available_days,
            "start_time": doc.start_time,
            "end_time": doc.end_time
        } for doc in docs]

    def get_recent_appointments(self) -> List[Dict[str, Any]]:
        """
        Retrieves the last 10 booked appointments.
        """
        try:
            # Query the 10 newest appointments (excluding Cancelled if desired, or just last 10 booked)
            appts = self.db.query(Appointment).order_by(
                Appointment.created_at.desc(),
                Appointment.appointment_date.desc(),
                Appointment.appointment_time.desc()
            ).limit(10).all()

            return [{
                "appointment_id": a.appointment_id,
                "patient_name": a.patient_name,
                "mobile": int(a.mobile) if a.mobile.isdigit() else a.mobile,
                "doctor_name": a.doctor_name,
                "department": a.department,
                "appointment_date": a.appointment_date,
                "appointment_time": a.appointment_time,
                "status": a.status,
                "created_at": a.created_at
            } for a in appts]
        except Exception as e:
            logger.error(f"Error querying recent appointments: {e}", exc_info=True)
            raise e
