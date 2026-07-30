from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from services.doctor_service import DoctorService
from services.hospital_service import HospitalService

router = APIRouter()

@router.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    """Retrieves all doctors from the database."""
    try:
        service = DoctorService(db)
        doctors = service.get_doctors()
        return {
            "success": True,
            "message": "Doctors retrieved successfully",
            "data": doctors
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve doctors",
                "errors": [str(e)]
            }
        )

@router.get("/hospital-info")
def get_hospital_info(db: Session = Depends(get_db)):
    """Retrieves hospital metadata information."""
    try:
        service = HospitalService(db)
        info = service.get_hospital_info()
        return {
            "success": True,
            "message": "Hospital info retrieved successfully",
            "data": info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve hospital info",
                "errors": [str(e)]
            }
        )

