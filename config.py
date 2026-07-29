import os
from pathlib import Path

# Base Directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
EXCEL_DB_PATH = DATABASE_DIR / "hospital_data.xlsx"

# Ensure the database directory exists
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Excel sheet names
DOCTORS_SHEET = "Doctors"
APPOINTMENTS_SHEET = "Appointments"
HOSPITAL_INFO_SHEET = "Hospital_Info"
