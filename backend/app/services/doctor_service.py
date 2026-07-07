
from sqlalchemy.orm import Session
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.core.security import hash_password
from typing import Optional
import json


class DoctorService:

    def create_doctor_profile(
        self,
        db: Session,
        user_id: int,
        specialty: str,
        consultation_fee: float,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        bio: Optional[str] = None,
        working_hours: Optional[dict] = None,
        appointment_duration_minutes: int = 30,
    ) -> Doctor:
        """إنشاء بروفايل دكتور جديد"""
        doctor = Doctor(
            user_id=user_id,
            specialty=specialty,
            consultation_fee=consultation_fee,
            phone=phone,
            location=location,
            bio=bio,
            working_hours=working_hours or {
                "Saturday":  ["09:00", "17:00"],
                "Sunday":    ["09:00", "17:00"],
                "Monday":    ["09:00", "17:00"],
                "Tuesday":   ["09:00", "17:00"],
                "Wednesday": ["09:00", "17:00"],
            },
            appointment_duration_minutes=appointment_duration_minutes,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        return doctor

    def get_all_doctors(self, db: Session) -> list:
        """جلب كل الدكاترة مع بياناتهم"""
        doctors = db.query(Doctor).join(
            User, Doctor.user_id == User.id
        ).filter(User.is_active == True).all()

        result = []
        for doc in doctors:
            user = db.query(User).filter(User.id == doc.user_id).first()
            result.append({
                "id": doc.id,
                "user_id": doc.user_id,
                "name": user.full_name,
                "email": user.email,
                "specialty": doc.specialty,
                "consultation_fee": doc.consultation_fee,
                "phone": doc.phone,
                "location": doc.location,
                "bio": doc.bio,
                "working_hours": doc.working_hours,
                "appointment_duration_minutes": doc.appointment_duration_minutes,
            })
        return result

    def get_doctor_by_id(self, db: Session, doctor_id: int) -> Optional[dict]:
        """جلب دكتور بالـ ID"""
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            return None
        user = db.query(User).filter(User.id == doc.user_id).first()
        return {
            "id": doc.id,
            "user_id": doc.user_id,
            "name": user.full_name if user else "",
            "email": user.email if user else "",
            "specialty": doc.specialty,
            "consultation_fee": doc.consultation_fee,
            "phone": doc.phone,
            "location": doc.location,
            "bio": doc.bio,
            "working_hours": doc.working_hours,
            "appointment_duration_minutes": doc.appointment_duration_minutes,
        }

    def update_doctor(self, db: Session, doctor_id: int, data: dict) -> Optional[Doctor]:
        """تحديث بيانات دكتور"""
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            return None
        for key, value in data.items():
            if hasattr(doc, key) and value is not None:
                setattr(doc, key, value)
        db.commit()
        db.refresh(doc)
        return doc


doctor_service = DoctorService()