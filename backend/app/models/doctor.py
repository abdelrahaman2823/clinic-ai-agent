from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialty = Column(String(100), nullable=False)       # تخصص الدكتور
    bio = Column(Text, nullable=True)                     # نبذة عن الدكتور
    consultation_fee = Column(Float, nullable=False)      # سعر الكشف
    phone = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)         # عنوان العيادة

    # مواعيد العمل - JSON: {"Saturday": ["09:00", "17:00"], "Sunday": [...]}
    working_hours = Column(JSON, nullable=True)

    # مدة كل موعد بالدقايق
    appointment_duration_minutes = Column(Integer, default=30)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")

    def __repr__(self):
        return f"<Doctor {self.specialty}>"