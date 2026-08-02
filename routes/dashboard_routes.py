import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import get_db
from services.dashboard_service import DashboardService
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard")

# Dependency
def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)

@router.get(
    "/stats",
    summary="Get dashboard statistics",
    description="Returns aggregate counts for today's active appointments, upcoming, cancelled, completed, and total doctors.",
    response_description="Dashboard counters metadata map."
)
def get_stats(service: DashboardService = Depends(get_dashboard_service)):
    try:
        stats = service.get_stats()
        return {
            "success": True,
            "message": "Dashboard stats retrieved successfully",
            "data": stats,
            "errors": []
        }
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve dashboard stats",
                "errors": [str(e)]
            }
        )

@router.get(
    "/appointments",
    summary="List paginated appointments",
    description="Retrieves sorted, filtered, and paginated appointments. Supports searching and date/doctor filtering.",
    response_description="Paginated list of appointment records."
)
def get_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Records per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. Booked, Rescheduled, Cancelled)"),
    doctor_id: Optional[str] = Query(None, description="Filter by Doctor ID"),
    date: Optional[str] = Query(None, description="Filter by Date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search term for patient name, mobile, or ID"),
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        res = service.get_paginated_appointments(
            page=page, 
            limit=limit, 
            status=status, 
            doctor_id=doctor_id, 
            date=date, 
            search=search
        )
        return {
            "success": True,
            "message": "Appointments retrieved successfully",
            "data": res,
            "errors": []
        }
    except Exception as e:
        logger.error(f"Failed to query paginated appointments: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to query appointments list",
                "errors": [str(e)]
            }
        )

@router.get(
    "/appointment/{appointment_id}",
    summary="Get complete appointment details",
    description="Retrieves the detailed record values of a single appointment.",
    response_description="A complete appointment profile record."
)
def get_appointment_detail(
    appointment_id: str,
    service: DashboardService = Depends(get_dashboard_service)
):
    try:
        appt = service.get_appointment_detail(appointment_id)
        if not appt:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Appointment not found",
                    "errors": [f"No appointment found with ID: '{appointment_id}'"]
                }
            )
        return {
            "success": True,
            "message": "Appointment details retrieved successfully",
            "data": appt,
            "errors": []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve appointment details: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve appointment details",
                "errors": [str(e)]
            }
        )

@router.get(
    "/doctors",
    summary="Get all dashboard doctors",
    description="Retrieves a list of all active doctor profiles for schedule configurations.",
    response_description="List of available doctors."
)
def get_doctors(service: DashboardService = Depends(get_dashboard_service)):
    try:
        doctors = service.get_doctors()
        return {
            "success": True,
            "message": "Doctors list retrieved successfully",
            "data": doctors,
            "errors": []
        }
    except Exception as e:
        logger.error(f"Failed to retrieve doctors list: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve doctors list",
                "errors": [str(e)]
            }
        )

@router.get(
    "/recent",
    summary="Get recently booked appointments",
    description="Retrieves the last 10 booked appointments in descending chronological order.",
    response_description="List of recent appointment records."
)
def get_recent(service: DashboardService = Depends(get_dashboard_service)):
    try:
        recent = service.get_recent_appointments()
        return {
            "success": True,
            "message": "Recent appointments retrieved successfully",
            "data": recent,
            "errors": []
        }
    except Exception as e:
        logger.error(f"Failed to retrieve recent appointments: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve recent appointments",
                "errors": [str(e)]
            }
        )
