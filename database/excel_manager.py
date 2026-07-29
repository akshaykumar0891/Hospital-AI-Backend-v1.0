import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import time, date, datetime
from config import EXCEL_DB_PATH, DOCTORS_SHEET, APPOINTMENTS_SHEET, HOSPITAL_INFO_SHEET

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class ExcelManager:
    def __init__(self, file_path: str = str(EXCEL_DB_PATH)):
        self.file_path = file_path
        logger.info(f"Initialized ExcelManager with database path: {self.file_path}")

    def _read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Reads a sheet and returns a clean DataFrame, or empty DataFrame if it doesn't exist."""
        if not os.path.exists(self.file_path):
            logger.error(f"Database file not found at {self.file_path}")
            raise FileNotFoundError(f"Database file not found at {self.file_path}")
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            if sheet_name == APPOINTMENTS_SHEET:
                columns = [
                    'Appointment ID', 'Patient Name', 'Mobile', 'Doctor ID', 
                    'Doctor Name', 'Department', 'Date', 'Time', 'Status', 
                    'Created At', 'Updated At', 'Cancelled At'
                ]
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                # Force columns to object dtype to prevent pandas LossySetitemError
                for col in columns:
                    df[col] = df[col].astype(object)
            return df
        except ValueError:
            logger.warning(f"Sheet {sheet_name} not found in workbook.")
            return pd.DataFrame()

    def _write_sheet(self, sheet_name: str, df: pd.DataFrame):
        """Writes a DataFrame to a specific sheet, preserving other sheets."""
        if not os.path.exists(self.file_path):
            logger.error(f"Database file not found at {self.file_path}")
            raise FileNotFoundError(f"Database file not found at {self.file_path}")
        
        # We use openpyxl to replace the sheet in the existing workbook
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Successfully wrote data to sheet {sheet_name}")

    def _clean_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Converts datetime.time, datetime.date, and float NaN objects to serializable formats."""
        cleaned = {}
        for k, v in row.items():
            if pd.isna(v):
                cleaned[k] = None
            elif isinstance(v, time):
                cleaned[k] = v.strftime("%H:%M")
            elif isinstance(v, (datetime, date)):
                # If datetime has non-zero time, format as datetime, otherwise date
                if isinstance(v, datetime) and v.time() != time(0, 0):
                    cleaned[k] = v.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    cleaned[k] = v.strftime("%Y-%m-%d")
            else:
                # If it's numpy int64 or similar, python type casting helps
                if hasattr(v, "item"):
                    cleaned[k] = v.item()
                else:
                    cleaned[k] = v
        return cleaned

    def get_doctors(self) -> List[Dict[str, Any]]:
        """Reads all doctors from the Excel workbook."""
        df = self._read_sheet(DOCTORS_SHEET)
        if df.empty:
            return []
        
        # Convert Slot Duration to int
        if "Slot Duration" in df.columns:
            df["Slot Duration"] = df["Slot Duration"].fillna(30).astype(int)
            
        records = df.to_dict(orient="records")
        return [self._clean_row(r) for r in records]

    def get_doctor_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by Doctor ID."""
        doctors = self.get_doctors()
        target_id = str(doctor_id).strip().lower()
        for doc in doctors:
            if str(doc.get("Doctor ID", "")).strip().lower() == target_id:
                return doc
        return None

    def get_doctor_by_name(self, doctor_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single doctor by Doctor Name (checks exact and normalized match)."""
        doctors = self.get_doctors()
        # Direct exact match check
        query = doctor_name.strip()
        for doc in doctors:
            if doc.get("Doctor Name") == query:
                return doc
                
        # Normalized case-insensitive check (ignoring Dr. prefix)
        query_norm = query.lower().replace("dr.", "").replace("dr", "").strip()
        for doc in doctors:
            doc_name = str(doc.get("Doctor Name", ""))
            doc_norm = doc_name.lower().replace("dr.", "").replace("dr", "").strip()
            if doc_norm == query_norm:
                return doc
        return None

    def get_appointments(self) -> List[Dict[str, Any]]:
        """Reads all appointments from the Excel workbook."""
        df = self._read_sheet(APPOINTMENTS_SHEET)
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        return [self._clean_row(r) for r in records]

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single appointment by Appointment ID."""
        appointments = self.get_appointments()
        target_id = str(appointment_id).strip().lower()
        for appt in appointments:
            if str(appt.get("Appointment ID", "")).strip().lower() == target_id:
                return appt
        return None

    def get_hospital_info(self) -> Dict[str, Any]:
        """Reads hospital info and returns it as a key-value dictionary."""
        df = self._read_sheet(HOSPITAL_INFO_SHEET)
        if df.empty:
            return {}
        # Columns: Key, Value
        records = df.to_dict(orient="records")
        info = {}
        for r in records:
            cleaned = self._clean_row(r)
            key = cleaned.get("Key")
            val = cleaned.get("Value")
            if key:
                info[key] = val
        return info

    def save_appointment(self, appointment_data: Dict[str, Any]):
        """Saves a new appointment by appending it to the Appointments sheet."""
        df = self._read_sheet(APPOINTMENTS_SHEET)
        
        # Ensure we construct the row matching standard and extra columns
        columns = [
            'Appointment ID', 'Patient Name', 'Mobile', 'Doctor ID', 
            'Doctor Name', 'Department', 'Date', 'Time', 'Status', 
            'Created At', 'Updated At', 'Cancelled At'
        ]
        
        # If Appointments is empty or missing columns, initialize with correct columns
        if df.empty or not all(c in df.columns for c in columns):
            df = pd.DataFrame(columns=columns)
            
        # Clean/format inputs before writing
        new_row = {col: appointment_data.get(col, None) for col in columns}
        
        # Set Created At timestamp if not provided
        if not new_row.get("Created At"):
            new_row["Created At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Append new row
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self._write_sheet(APPOINTMENTS_SHEET, new_df)
        logger.info(f"Saved new appointment {appointment_data.get('Appointment ID')}")

    def update_appointment(self, appointment_id: str, updated_fields: Dict[str, Any]) -> bool:
        """Updates an existing appointment by Appointment ID with updated fields."""
        df = self._read_sheet(APPOINTMENTS_SHEET)
        if df.empty:
            logger.warning("Attempted to update appointment in empty table")
            return False
            
        # Ensure Appointment ID is compared as string
        df["Appointment ID"] = df["Appointment ID"].astype(str)
        target_id = str(appointment_id)
        
        # Find index where Appointment ID matches
        match_idx = df.index[df["Appointment ID"] == target_id].tolist()
        if not match_idx:
            logger.warning(f"Appointment ID {appointment_id} not found for update")
            return False
            
        idx = match_idx[0]
        # Update columns
        for key, val in updated_fields.items():
            if key in df.columns:
                df.at[idx, key] = val
                
        self._write_sheet(APPOINTMENTS_SHEET, df)
        logger.info(f"Updated appointment {appointment_id}")
        return True

    def delete_appointment(self, appointment_id: str) -> bool:
        """Deletes an appointment by Appointment ID."""
        df = self._read_sheet(APPOINTMENTS_SHEET)
        if df.empty:
            logger.warning("Attempted to delete appointment from empty table")
            return False
            
        df["Appointment ID"] = df["Appointment ID"].astype(str)
        target_id = str(appointment_id)
        
        initial_len = len(df)
        df = df[df["Appointment ID"] != target_id]
        
        if len(df) == initial_len:
            logger.warning(f"Appointment ID {appointment_id} not found for deletion")
            return False
            
        self._write_sheet(APPOINTMENTS_SHEET, df)
        logger.info(f"Successfully deleted appointment {appointment_id}")
        return True


