
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_doctor
from app.models.user import User
from app.services.appointment_service import appointment_service
from app.services.doctor_service import doctor_service
from app.services.google_sheets import sheets_service

router = APIRouter(prefix="/sync", tags=["Google Sheets Sync"])


@router.post("/all")
def sync_everything(
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """مزامنة كل الداتا مع Google Sheets"""
    # مزامنة المواعيد
    all_appointments = appointment_service.get_all_appointments(db)
    sheets_service.sync_all_appointments(all_appointments)

    # مزامنة الدكاترة
    all_doctors = doctor_service.get_all_doctors(db)
    sheets_service.sync_doctors(all_doctors)

    return {
        "message": "تمت المزامنة بنجاح",
        "appointments_synced": len(all_appointments),
        "doctors_synced": len(all_doctors),
    }


@router.post("/setup")
def setup_sheets(
    current_user: User = Depends(require_doctor),
):
    """إعداد الـ Google Sheets لأول مرة"""
    sheets_service.setup_all_sheets()
    return {"message": "تم إعداد الـ Google Sheets بنجاح"}