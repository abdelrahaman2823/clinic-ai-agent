
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import require_secretary
from app.models.user import User, UserRole

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/")
def get_all_patients(
    search: Optional[str] = Query(None, description="ابحث باسم أو تليفون"),
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """جلب كل المرضى — للسيكرتير والدكتور"""
    query = db.query(User).filter(User.role == UserRole.patient)

    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    patients = query.order_by(User.full_name).all()

    return [
        {
            "id": p.id,
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
        for p in patients
    ]


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """جلب مريض بالـ ID مع كل مواعيده"""
    patient = db.query(User).filter(
        User.id == patient_id,
        User.role == UserRole.patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="المريض ده مش موجود")

    from app.services.appointment_service import appointment_service
    appointments = appointment_service.get_appointments_for_patient(db, patient_id)

    return {
        "id": patient.id,
        "full_name": patient.full_name,
        "email": patient.email,
        "phone": patient.phone,
        "is_active": patient.is_active,
        "created_at": patient.created_at.isoformat() if patient.created_at else "",
        "appointments": appointments,
        "total_appointments": len(appointments),
    }


@router.patch("/{patient_id}/deactivate")
def deactivate_patient(
    patient_id: int,
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """إيقاف حساب مريض"""
    patient = db.query(User).filter(
        User.id == patient_id,
        User.role == UserRole.patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="المريض ده مش موجود")

    patient.is_active = False
    db.commit()
    return {"message": "تم إيقاف الحساب"}