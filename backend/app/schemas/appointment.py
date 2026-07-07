from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: datetime
    patient_notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    doctor_notes: Optional[str] = None
    appointment_date: Optional[datetime] = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    status: AppointmentStatus
    patient_notes: Optional[str]
    doctor_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True