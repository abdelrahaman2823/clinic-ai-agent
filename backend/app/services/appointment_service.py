
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.user import User
from app.services.google_sheets import sheets_service
from datetime import datetime, timedelta
from typing import Optional, List


class AppointmentService:

    def get_appointments_for_doctor(
        self,
        db: Session,
        doctor_id: int,
        date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[dict]:
        """جلب مواعيد دكتور معين مع فلتر اختياري"""
        query = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id
        )

        if date:
            target = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(
                and_(
                    Appointment.appointment_date >= target,
                    Appointment.appointment_date < target + timedelta(days=1)
                )
            )

        if status:
            query = query.filter(Appointment.status == status)

        appointments = query.order_by(Appointment.appointment_date).all()
        return self._format_appointments(db, appointments)

    def get_appointments_for_patient(
        self,
        db: Session,
        patient_id: int,
    ) -> List[dict]:
        """جلب كل مواعيد مريض"""
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.appointment_date.desc()).all()
        return self._format_appointments(db, appointments)

    def get_all_appointments(
        self,
        db: Session,
        date: Optional[str] = None,
        status: Optional[str] = None,
        doctor_id: Optional[int] = None,
    ) -> List[dict]:
        """جلب كل المواعيد — للسيكرتير والدكتور"""
        query = db.query(Appointment)

        if date:
            target = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(
                and_(
                    Appointment.appointment_date >= target,
                    Appointment.appointment_date < target + timedelta(days=1)
                )
            )
        if status:
            query = query.filter(Appointment.status == status)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        appointments = query.order_by(Appointment.appointment_date).all()
        return self._format_appointments(db, appointments)

    def update_appointment_status(
        self,
        db: Session,
        appointment_id: int,
        new_status: AppointmentStatus,
        doctor_notes: Optional[str] = None,
    ) -> Optional[dict]:
        """تحديث حالة الموعد"""
        apt = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not apt:
            return None

        apt.status = new_status
        if doctor_notes:
            apt.doctor_notes = doctor_notes

        db.commit()
        db.refresh(apt)

        # مزامنة Google Sheets
        try:
            if apt.sheets_row_id:
                sheets_service.update_appointment_status(
                    apt.sheets_row_id, new_status.value
                )
        except Exception:
            pass

        return self._format_single(db, apt)

    def reschedule_appointment(
        self,
        db: Session,
        appointment_id: int,
        new_date: str,
        new_time: str,
    ) -> Optional[dict]:
        """إعادة جدولة موعد"""
        apt = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not apt:
            return None

        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")

        # التحقق من عدم وجود تعارض
        conflict = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == apt.doctor_id,
                Appointment.appointment_date == new_datetime,
                Appointment.status.in_([
                    AppointmentStatus.pending,
                    AppointmentStatus.confirmed
                ]),
                Appointment.id != appointment_id
            )
        ).first()

        if conflict:
            return {"error": "الموعد ده محجوز بالفعل"}

        apt.appointment_date = new_datetime
        apt.status = AppointmentStatus.pending
        db.commit()
        db.refresh(apt)

        # تحديث Google Sheets
        try:
            if apt.sheets_row_id:
                sheets_service.update_appointment_status(
                    apt.sheets_row_id, "rescheduled"
                )
        except Exception:
            pass

        return self._format_single(db, apt)

    def get_today_appointments(self, db: Session, doctor_id: Optional[int] = None) -> List[dict]:
        """جلب مواعيد النهارده"""
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        return self.get_all_appointments(db, date=today_str, doctor_id=doctor_id)

    def get_appointment_stats(self, db: Session, doctor_id: Optional[int] = None) -> dict:
        """إحصائيات المواعيد"""
        query = db.query(Appointment)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        total = query.count()
        pending = query.filter(Appointment.status == AppointmentStatus.pending).count()
        confirmed = query.filter(Appointment.status == AppointmentStatus.confirmed).count()
        cancelled = query.filter(Appointment.status == AppointmentStatus.cancelled).count()
        completed = query.filter(Appointment.status == AppointmentStatus.completed).count()

        # مواعيد النهارده
        today = datetime.now().date()
        today_count = query.filter(
            and_(
                Appointment.appointment_date >= datetime.combine(today, datetime.min.time()),
                Appointment.appointment_date < datetime.combine(today, datetime.max.time()),
            )
        ).count()

        return {
            "total": total,
            "today": today_count,
            "pending": pending,
            "confirmed": confirmed,
            "cancelled": cancelled,
            "completed": completed,
        }

    def _format_appointments(self, db: Session, appointments: list) -> List[dict]:
        return [self._format_single(db, apt) for apt in appointments]

    def _format_single(self, db: Session, apt: Appointment) -> dict:
        patient = db.query(User).filter(User.id == apt.patient_id).first()
        doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        doctor_user = db.query(User).filter(
            User.id == doctor.user_id
        ).first() if doctor else None

        return {
            "id": apt.id,
            "patient_id": apt.patient_id,
            "patient_name": patient.full_name if patient else "غير محدد",
            "patient_phone": patient.phone if patient else "",
            "patient_email": patient.email if patient else "",
            "doctor_id": apt.doctor_id,
            "doctor_name": doctor_user.full_name if doctor_user else "غير محدد",
            "doctor_specialty": doctor.specialty if doctor else "",
            "appointment_date": apt.appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": apt.appointment_date.strftime("%H:%M"),
            "appointment_datetime": apt.appointment_date.isoformat(),
            "status": apt.status.value,
            "patient_notes": apt.patient_notes or "",
            "doctor_notes": apt.doctor_notes or "",
            "created_at": apt.created_at.isoformat() if apt.created_at else "",
        }


appointment_service = AppointmentService()