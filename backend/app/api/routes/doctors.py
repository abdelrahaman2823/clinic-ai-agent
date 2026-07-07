
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_doctor
from app.models.user import User, UserRole
from app.services.doctor_service import doctor_service
from app.core.security import hash_password

router = APIRouter(prefix="/doctors", tags=["Doctors"])


class DoctorRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None
    specialty: str
    consultation_fee: float
    location: Optional[str] = None
    bio: Optional[str] = None
    appointment_duration_minutes: int = 30
    working_hours: Optional[dict] = None


class DoctorUpdateRequest(BaseModel):
    specialty: Optional[str] = None
    consultation_fee: Optional[float] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    working_hours: Optional[dict] = None
    appointment_duration_minutes: Optional[int] = None


@router.post("/register", status_code=201)
def register_doctor(
    data: DoctorRegisterRequest,
    db: Session = Depends(get_db),
):
    """تسجيل دكتور جديد مع بروفايله"""
    # التحقق من عدم تكرار الإيميل
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="الإيميل ده موجود بالفعل")

    # إنشاء الـ user
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role=UserRole.doctor,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # إنشاء بروفايل الدكتور
    doctor = doctor_service.create_doctor_profile(
        db=db,
        user_id=user.id,
        specialty=data.specialty,
        consultation_fee=data.consultation_fee,
        phone=data.phone,
        location=data.location,
        bio=data.bio,
        working_hours=data.working_hours,
        appointment_duration_minutes=data.appointment_duration_minutes,
    )

    return {
        "message": "تم تسجيل الدكتور بنجاح",
        "user_id": user.id,
        "doctor_id": doctor.id,
    }


@router.get("/")
def get_all_doctors(db: Session = Depends(get_db)):
    """جلب كل الدكاترة — متاح للجميع"""
    return doctor_service.get_all_doctors(db)


@router.get("/{doctor_id}")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """جلب دكتور بالـ ID"""
    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="الدكتور ده مش موجود")
    return doc


@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: DoctorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    """تحديث بيانات الدكتور — الدكتور نفسه بس"""
    updated = doctor_service.update_doctor(db, doctor_id, data.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="الدكتور ده مش موجود")
    return {"message": "تم التحديث بنجاح"}