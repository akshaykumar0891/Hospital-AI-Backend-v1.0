import logging
from sqlalchemy.orm import Session
from database.models import Doctor
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DoctorService:
    def __init__(self, db: Session):
        self.db = db

    def get_doctors(self) -> List[Dict[str, Any]]:
        """Retrieves all doctors from the database as dictionaries."""
        docs = self.db.query(Doctor).all()
        return [{
            "Doctor ID": doc.doctor_id,
            "Doctor Name": doc.doctor_name,
            "Department": doc.department,
            "Available Days": doc.available_days,
            "Start Time": doc.start_time,
            "End Time": doc.end_time,
            "Slot Duration": doc.slot_duration
        } for doc in docs]

    def get_doctor_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by Doctor ID as a dictionary."""
        doc = self.db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
        if not doc:
            return None
        return {
            "Doctor ID": doc.doctor_id,
            "Doctor Name": doc.doctor_name,
            "Department": doc.department,
            "Available Days": doc.available_days,
            "Start Time": doc.start_time,
            "End Time": doc.end_time,
            "Slot Duration": doc.slot_duration
        }

    def get_doctor_by_name(self, doctor_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by Doctor Name (checks exact and normalized match)."""
        docs = self.get_doctors()
        query = doctor_name.strip()
        
        # 1. Exact match check
        for doc in docs:
            if doc.get("Doctor Name") == query:
                return doc
                
        # 2. Normalized check (case insensitive & ignoring "Dr." prefix)
        query_norm = query.lower().replace("dr.", "").replace("dr", "").strip()
        for doc in docs:
            doc_name = str(doc.get("Doctor Name", ""))
            doc_norm = doc_name.lower().replace("dr.", "").replace("dr", "").strip()
            if doc_norm == query_norm:
                return doc
        return None
