from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional


from services.availability_service import AvailabilityService
from services.booking_service import BookingService
from services.appointment_service import AppointmentService
from models.appointment import AppointmentCreate, AppointmentReschedule

router = APIRouter()

# Request schemas for simple POST requests
class AvailabilityRequest(BaseModel):
    doctor_id: str
    date: str

class CancelRequest(BaseModel):
    appointment_id: str

from sqlalchemy.orm import Session
from database.database import get_db

# Dependencies
def get_availability_service(db: Session = Depends(get_db)) -> AvailabilityService:
    return AvailabilityService(db)

def get_booking_service(db: Session = Depends(get_db), avail: AvailabilityService = Depends(get_availability_service)) -> BookingService:
    return BookingService(db, avail)

def get_appointment_service(db: Session = Depends(get_db), avail: AvailabilityService = Depends(get_availability_service)) -> AppointmentService:
    return AppointmentService(db, avail)



@router.post("/check-availability")
def check_availability(req: AvailabilityRequest, avail: AvailabilityService = Depends(get_availability_service)):
    """Checks slots availability for a doctor on a specific date."""
    res = avail.get_available_slots(req.doctor_id, req.date)
    if res.get("status") == "error":
        return {
            "success": False,
            "message": res.get("message"),
            "errors": [res.get("message")]
        }
    return {
        "success": True,
        "message": f"Availability check completed for doctor ID {req.doctor_id}",
        "data": res
    }

@router.post("/book-appointment")
def book_appointment(req: AppointmentCreate, booking_srv: BookingService = Depends(get_booking_service)):
    """Books a new appointment after validations and availability checks."""
    # Convert model to dict for booking service
    booking_data = req.model_dump()
    res = booking_srv.book_appointment(booking_data)
    
    if not res.get("success"):
        # Return structured error shape
        return {
            "success": False,
            "message": res.get("message"),
            "data": {
                "available_slots": res.get("available_slots", []),
                "next_available_date": res.get("next_available_date", None)
            }
        }
    
    return {
        "success": True,
        "message": res.get("message"),
        "data": {
            "appointment_id": res.get("appointment_id")
        }
    }

@router.post("/cancel-appointment")
def cancel_appointment(req: CancelRequest, appt_srv: AppointmentService = Depends(get_appointment_service)):
    """Cancels an existing appointment (soft-delete)."""
    res = appt_srv.cancel_appointment(req.appointment_id)
    if not res.get("success"):
        return {
            "success": False,
            "message": res.get("message")
        }
    return {
        "success": True,
        "message": res.get("message"),
        "data": {
            "appointment_id": res.get("appointment_id")
        }
    }

@router.post("/reschedule-appointment")
def reschedule_appointment(req: AppointmentReschedule, appt_srv: AppointmentService = Depends(get_appointment_service)):
    """Reschedules an existing active appointment."""
    res = appt_srv.reschedule_appointment(req.appointment_id, req.new_date, req.new_time)
    if not res.get("success"):
        return {
            "success": False,
            "message": res.get("message"),
            "data": {
                "available_slots": res.get("available_slots", []),
                "next_available_date": res.get("next_available_date", None)
            }
        }
    return {
        "success": True,
        "message": res.get("message"),
        "data": {
            "appointment_id": res.get("appointment_id")
        }
    }

@router.get("/appointment-status")
def get_appointment_status(
    appointment_id: Optional[str] = Query(None, description="Search by unique Appointment ID"),
    mobile: Optional[str] = Query(None, description="Search by registered Mobile Number"),
    appt_srv: AppointmentService = Depends(get_appointment_service)
):
    """Retrieves appointment state by Appointment ID or Mobile Number."""
    if not appointment_id and not mobile:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Must provide either appointment_id or mobile number query parameter."
            }
        )
    
    res = appt_srv.get_appointment_status(appointment_id=appointment_id, mobile=mobile)
    if not res.get("success"):
        return {
            "success": False,
            "message": res.get("message")
        }
        
    return {
        "success": True,
        "message": "Appointments retrieved successfully",
        "data": {
            "appointments": res.get("appointments")
        }
    }
