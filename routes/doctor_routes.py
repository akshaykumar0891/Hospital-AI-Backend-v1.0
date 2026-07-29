from fastapi import APIRouter, Depends, HTTPException
from database.excel_manager import ExcelManager

router = APIRouter()

def get_excel_manager() -> ExcelManager:
    return ExcelManager()

@router.get("/doctors")
def get_doctors(db: ExcelManager = Depends(get_excel_manager)):
    """Retrieves all doctors from the excel sheet database."""
    try:
        doctors = db.get_doctors()
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
def get_hospital_info(db: ExcelManager = Depends(get_excel_manager)):
    """Retrieves hospital metadata information."""
    try:
        info = db.get_hospital_info()
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
