from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AppointmentStatus(str, enum.Enum):
    pending = "pending"         # في الانتظار
    confirmed = "confirmed"     # مؤكد
    cancelled = "cancelled"     # ملغي
    completed = "completed"     # اتم
    no_show = "no_show"         # البيشنت معجاش


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    # التاريخ والوقت
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.pending,
        nullable=False
    )

    # ملاحظات
    patient_notes = Column(Text, nullable=True)    # البيشنت يكتب شكواه
    doctor_notes = Column(Text, nullable=True)      # الدكتور يكتب ملاحظاته

    # Google Sheets row ID للـ sync
    sheets_row_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="appointments_as_patient")
    doctor = relationship("Doctor", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment {self.id} - {self.status}>"