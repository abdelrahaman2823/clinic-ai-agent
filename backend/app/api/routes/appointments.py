
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_doctor, require_secretary
from app.models.user import User, UserRole
from app.models.appointment import AppointmentStatus
from app.services.appointment_service import appointment_service
from app.services.notification_service import notification_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class StatusUpdateRequest(BaseModel):
    status: AppointmentStatus
    doctor_notes: Optional[str] = None


class RescheduleRequest(BaseModel):
    new_date: str   # YYYY-MM-DD
    new_time: str   # HH:MM


# ══ Patient Routes ══

@router.get("/my")
def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """البيشنت يشوف مواعيده"""
    return appointment_service.get_appointments_for_patient(db, current_user.id)


# ══ Secretary & Doctor Routes ══

@router.get("/")
def get_all_appointments(
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    status: Optional[str] = Query(None),
    doctor_id: Optional[int] = Query(None),
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """جلب كل المواعيد مع فلتر — للسيكرتير والدكتور"""
    return appointment_service.get_all_appointments(db, date, status, doctor_id)


@router.get("/today")
def get_today_appointments(
    doctor_id: Optional[int] = Query(None),
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """مواعيد النهارده"""
    return appointment_service.get_today_appointments(db, doctor_id)


@router.get("/stats")
def get_stats(
    doctor_id: Optional[int] = Query(None),
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """إحصائيات المواعيد"""
    return appointment_service.get_appointment_stats(db, doctor_id)


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """جلب موعد بالـ ID"""
    from app.models.appointment import Appointment
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="الموعد ده مش موجود")

    # البيشنت يشوف مواعيده بس
    if current_user.role == UserRole.patient and apt.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="مش مسموح")

    return appointment_service._format_single(db, apt)


@router.patch("/{appointment_id}/status")
def update_status(
    appointment_id: int,
    data: StatusUpdateRequest,
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """تحديث حالة الموعد — للدكتور والسيكرتير"""
    result = appointment_service.update_appointment_status(
        db, appointment_id, data.status, data.doctor_notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="الموعد ده مش موجود")

    # إشعار لو اتأكد أو اتلغى
    if data.status == AppointmentStatus.confirmed:
        notification_service.send_booking_confirmation(
            patient_name=result["patient_name"],
            patient_phone=result["patient_phone"],
            doctor_name=result["doctor_name"],
            appointment_date=result["appointment_date"],
            appointment_time=result["appointment_time"],
            appointment_id=appointment_id,
        )
    elif data.status == AppointmentStatus.cancelled:
        notification_service.send_cancellation_notice(
            patient_name=result["patient_name"],
            patient_phone=result["patient_phone"],
            appointment_id=appointment_id,
        )

    return {"message": "تم التحديث بنجاح", "appointment": result}


@router.patch("/{appointment_id}/reschedule")
def reschedule(
    appointment_id: int,
    data: RescheduleRequest,
    current_user: User = Depends(require_secretary),
    db: Session = Depends(get_db),
):
    """إعادة جدولة موعد"""
    result = appointment_service.reschedule_appointment(
        db, appointment_id, data.new_date, data.new_time
    )
    if not result:
        raise HTTPException(status_code=404, detail="الموعد ده مش موجود")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": "تم إعادة الجدولة بنجاح", "appointment": result}


@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """إلغاء موعد — البيشنت يلغي بتاعه، الدكتور والسيكرتير يلغوا أي حاجة"""
    from app.models.appointment import Appointment
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not apt:
        raise HTTPException(status_code=404, detail="الموعد ده مش موجود")

    if current_user.role == UserRole.patient and apt.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="مش مسموح تلغي موعد مش بتاعك")

    result = appointment_service.update_appointment_status(
        db, appointment_id, AppointmentStatus.cancelled
    )

    notification_service.send_cancellation_notice(
        patient_name=result["patient_name"],
        patient_phone=result["patient_phone"],
        appointment_id=appointment_id,
    )

    return {"message": "تم الإلغاء بنجاح"}