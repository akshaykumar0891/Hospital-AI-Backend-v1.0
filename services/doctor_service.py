import logging
from sqlalchemy.orm import Session
from database.models import Doctor
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Specialization/Department Synonym Mapping
SYNONYM_MAP = {
    # Cardiology
    "cardiologist": "Cardiology",
    "cardio": "Cardiology",
    "heart doctor": "Cardiology",
    "heart specialist": "Cardiology",
    
    # Pediatrics
    "children doctor": "Pediatrics",
    "child doctor": "Pediatrics",
    "kids doctor": "Pediatrics",
    "pediatrician": "Pediatrics",
    "children specialist": "Pediatrics",
    "kids specialist": "Pediatrics",
    
    # General Medicine
    "general physician": "General Medicine",
    "general doctor": "General Medicine",
    "physician": "General Medicine",
    "medicine doctor": "General Medicine",
    "general medicine": "General Medicine",
    "gp": "General Medicine",
    "medicine": "General Medicine",
    "family doctor": "General Medicine"
}

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

    def clean_name_for_comparison(self, name: str) -> str:
        """Helper to normalize a name by converting to lowercase, removing 'dr.'/'dr', and stripping spaces."""
        cleaned = name.lower().strip()
        # Remove common prefixes
        if cleaned.startswith("dr."):
            cleaned = cleaned[3:].strip()
        elif cleaned.startswith("dr"):
            cleaned = cleaned[2:].strip()
        # Remove extra whitespace between words
        return " ".join(cleaned.split())

    def get_doctor_by_name(self, doctor_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by Doctor Name (checks exact and normalized match)."""
        docs = self.get_doctors()
        query = doctor_name.strip()
        
        # 1. Exact match check
        for doc in docs:
            if doc.get("Doctor Name") == query:
                return doc
                
        # 2. Normalized check (case insensitive & ignoring "Dr." prefix)
        query_norm = self.clean_name_for_comparison(query)
        for doc in docs:
            doc_name = str(doc.get("Doctor Name", ""))
            doc_norm = self.clean_name_for_comparison(doc_name)
            
            # Match if normalized full names are equal, OR if query is a token/part of doctor name
            if doc_norm == query_norm or query_norm in doc_norm or doc_norm in query_norm:
                return doc
        return None

    def search_doctors(self, query: str) -> List[Dict[str, Any]]:
        """
        Flexible search for doctors by name, department, or specialization synonyms.
        """
        logger.info(f"Doctor search initiated for query: '{query}'")
        if not query:
            return []

        cleaned_query = query.lower().strip()
        
        # Check synonym map first
        target_department = None
        for syn, dept in SYNONYM_MAP.items():
            if syn in cleaned_query or cleaned_query in syn:
                target_department = dept
                break
        
        docs = self.get_doctors()
        matched = []
        
        query_norm = self.clean_name_for_comparison(query)

        for doc in docs:
            doc_name_cleaned = self.clean_name_for_comparison(doc["Doctor Name"])
            doc_dept = doc["Department"].lower()
            
            # Check matches:
            # 1. Department matches synonym target
            # 2. Query name tokens are present in doctor's normalized name (or vice versa)
            # 3. Direct department match
            if (target_department and doc["Department"].lower() == target_department.lower()) or \
               (query_norm in doc_name_cleaned or doc_name_cleaned in query_norm) or \
               (cleaned_query in doc_dept or doc_dept in cleaned_query):
                matched.append(doc)
                
        return matched
