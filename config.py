import os
from pathlib import Path

# Base Directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Hospital Metadata Configurations
HOSPITAL_NAME = "ABC Hospital"
TIMEZONE = "Asia/Kolkata"
DEFAULT_SLOT_DURATION = 30
DEFAULT_START_TIME = "09:00"
DEFAULT_END_TIME = "20:00"
APPOINTMENT_LIMITS_DAYS = 14

# Standard Hospital Holidays (YYYY-MM-DD)
HOLIDAYS = [
    "2026-08-15",  # Independence Day
    "2026-01-26",  # Republic Day
    "2026-10-02",  # Gandhi Jayanti
    "2026-12-25",  # Christmas
]
