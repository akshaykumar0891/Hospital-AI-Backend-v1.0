from pydantic import BaseModel, Field
from typing import Optional

class Appointment(BaseModel):
    appointment_id: str = Field(alias="Appointment ID")
    patient_name: str = Field(alias="Patient Name")
    mobile: str = Field(alias="Mobile")
    doctor_id: str = Field(alias="Doctor ID")
    doctor_name: str = Field(alias="Doctor Name")
    department: str = Field(alias="Department")
    date: str = Field(alias="Date")
    time: str = Field(alias="Time")
    status: str = Field(alias="Status")
    created_at: str = Field(alias="Created At")
    updated_at: Optional[str] = Field(default=None, alias="Updated At")
    cancelled_at: Optional[str] = Field(default=None, alias="Cancelled At")

    model_config = {
        "populate_by_name": True
    }

class AppointmentCreate(BaseModel):
    patient_name: str = Field(..., min_length=1)
    mobile: str = Field(..., min_length=5)
    doctor_name: str = Field(..., min_length=1)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}(:\d{2})?$")

class AppointmentReschedule(BaseModel):
    appointment_id: str = Field(..., min_length=1)
    new_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    new_time: str = Field(..., pattern=r"^\d{2}:\d{2}(:\d{2})?$")

