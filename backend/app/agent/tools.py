# backend/app/agent/tools.py

from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.doctor import Doctor
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus
from app.services.google_sheets import sheets_service
from datetime import datetime
from typing import Optional
import json


def get_db_session() -> Session:
    return SessionLocal()


@tool
def get_all_doctors() -> str:
    """
    جلب قائمة كل الدكاترة المتاحين في العيادة مع معلوماتهم.
    استخدم الـ tool ده لما المريض يسأل عن الدكاترة المتاحين.
    """
    db = get_db_session()
    try:
        doctors = db.query(Doctor).join(User, Doctor.user_id == User.id).filter(
            User.is_active == True
        ).all()

        if not doctors:
            return "مفيش دكاترة متاحين دلوقتي."

        result = []
        for doc in doctors:
            user = db.query(User).filter(User.id == doc.user_id).first()
            result.append({
                "id": doc.id,
                "name": user.full_name if user else "غير معروف",
                "specialty": doc.specialty,
                "fee": doc.consultation_fee,
                "phone": doc.phone or "غير متاح",
                "location": doc.location or "غير محدد",
                "appointment_duration": doc.appointment_duration_minutes,
            })

        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def get_doctor_info(doctor_name: str) -> str:
    """
    جلب معلومات دكتور معين بالاسم.
    استخدم الـ tool ده لما المريض يسأل عن دكتور بالاسم.

    Args:
        doctor_name: اسم الدكتور أو جزء منه
    """
    db = get_db_session()
    try:
        users = db.query(User).filter(
            User.full_name.ilike(f"%{doctor_name}%"),
            User.role == "doctor"
        ).all()

        if not users:
            return f"مفيش دكتور بالاسم ده: {doctor_name}"

        result = []
        for user in users:
            doc = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if doc:
                working_hours_text = "غير محدد"
                if doc.working_hours:
                    days = []
                    for day, hours in doc.working_hours.items():
                        days.append(f"{day}: من {hours[0]} لـ {hours[1]}")
                    working_hours_text = " | ".join(days)

                result.append({
                    "id": doc.id,
                    "name": user.full_name,
                    "specialty": doc.specialty,
                    "fee": f"{doc.consultation_fee} جنيه",
                    "phone": doc.phone or "غير متاح",
                    "location": doc.location or "غير محدد",
                    "working_hours": working_hours_text,
                    "appointment_duration": f"{doc.appointment_duration_minutes} دقيقة",
                })

        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def check_availability(doctor_id: int, date: str) -> str:
    """
    التحقق من المواعيد المتاحة لدكتور معين في يوم معين.

    Args:
        doctor_id: رقم الدكتور
        date: التاريخ بصيغة YYYY-MM-DD مثل 2024-12-25
    """
    db = get_db_session()
    try:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return "الدكتور ده مش موجود."

        # جلب المواعيد المحجوزة في اليوم ده
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "صيغة التاريخ غلط، استخدم YYYY-MM-DD مثل 2024-12-25"

        booked = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([
                AppointmentStatus.pending,
                AppointmentStatus.confirmed
            ])
        ).all()

        booked_times = []
        for apt in booked:
            if apt.appointment_date.date() == target_date.date():
                booked_times.append(apt.appointment_date.strftime("%H:%M"))

        # المواعيد المتاحة بناءً على working_hours
        available_slots = []
        day_name_ar = {
            "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين",
            "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
            "Thursday": "الخميس", "Friday": "الجمعة"
        }
        day_en = target_date.strftime("%A")

        if doctor.working_hours and day_en in doctor.working_hours:
            hours = doctor.working_hours[day_en]
            start = datetime.strptime(hours[0], "%H:%M")
            end = datetime.strptime(hours[1], "%H:%M")
            duration = doctor.appointment_duration_minutes

            current = start
            while current < end:
                slot = current.strftime("%H:%M")
                if slot not in booked_times:
                    available_slots.append(slot)
                current = current.replace(
                    hour=current.hour + (current.minute + duration) // 60,
                    minute=(current.minute + duration) % 60
                )

            if not available_slots:
                return f"مفيش مواعيد متاحة يوم {day_name_ar.get(day_en, day_en)} {date}"

            return f"المواعيد المتاحة يوم {day_name_ar.get(day_en, day_en)} {date}:\n" + \
                   "\n".join([f"- {slot}" for slot in available_slots])
        else:
            return f"الدكتور مش بيشتغل يوم {day_name_ar.get(day_en, day_en)}"

    finally:
        db.close()


@tool
def book_appointment(
    patient_id: int,
    doctor_id: int,
    date: str,
    time: str,
    notes: Optional[str] = None
) -> str:
    """
    حجز موعد جديد للمريض.

    Args:
        patient_id: رقم المريض
        doctor_id: رقم الدكتور
        date: التاريخ بصيغة YYYY-MM-DD
        time: الوقت بصيغة HH:MM
        notes: ملاحظات اختيارية
    """
    db = get_db_session()
    try:
        # التحقق من وجود الدكتور والمريض
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        patient = db.query(User).filter(User.id == patient_id).first()

        if not doctor:
            return "الدكتور ده مش موجود."
        if not patient:
            return "المريض ده مش موجود."

        # دمج التاريخ والوقت
        try:
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "صيغة التاريخ أو الوقت غلط."

        # التحقق إن الموعد مش محجوز
        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_datetime,
            Appointment.status.in_([
                AppointmentStatus.pending,
                AppointmentStatus.confirmed
            ])
        ).first()

        if existing:
            return f"الموعد ده محجوز بالفعل. اختار وقت تاني."

        # إنشاء الحجز
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_datetime,
            status=AppointmentStatus.pending,
            patient_notes=notes,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # مزامنة مع Google Sheets
        doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
        try:
            row_id = sheets_service.append_appointment({
                "id": appointment.id,
                "patient_name": patient.full_name,
                "patient_phone": patient.phone or "",
                "doctor_name": doctor_user.full_name if doctor_user else "",
                "appointment_date": appointment_datetime.strftime("%Y-%m-%d %H:%M"),
                "status": "pending",
                "patient_notes": notes or "",
            })
            appointment.sheets_row_id = row_id
            db.commit()
        except Exception:
            pass  # لو الـ Sheets فشل، الحجز بيتم عادي في الـ DB

        return f"""✅ تم الحجز بنجاح!
رقم الحجز: #{appointment.id}
الدكتور: {doctor_user.full_name if doctor_user else 'غير محدد'}
التاريخ: {date}
الوقت: {time}
الحالة: في الانتظار
"""
    finally:
        db.close()


@tool
def cancel_appointment(appointment_id: int, patient_id: int) -> str:
    """
    إلغاء حجز موجود.

    Args:
        appointment_id: رقم الحجز
        patient_id: رقم المريض (للتأكد إنه صاحب الحجز)
    """
    db = get_db_session()
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id
        ).first()

        if not appointment:
            return "الحجز ده مش موجود أو مش بتاعك."

        if appointment.status == AppointmentStatus.cancelled:
            return "الحجز ده ملغي أصلاً."

        if appointment.status == AppointmentStatus.completed:
            return "مينفعش تلغي حجز اتم."

        appointment.status = AppointmentStatus.cancelled
        db.commit()

        # تحديث Google Sheets
        try:
            if appointment.sheets_row_id:
                sheets_service.update_appointment_status(
                    appointment.sheets_row_id, "cancelled"
                )
        except Exception:
            pass

        return f"✅ تم إلغاء الحجز #{appointment_id} بنجاح."
    finally:
        db.close()


@tool
def get_patient_appointments(patient_id: int) -> str:
    """
    جلب كل مواعيد المريض.

    Args:
        patient_id: رقم المريض
    """
    db = get_db_session()
    try:
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status.in_([
                AppointmentStatus.pending,
                AppointmentStatus.confirmed
            ])
        ).order_by(Appointment.appointment_date).all()

        if not appointments:
            return "مفيش مواعيد قادمة."

        result = []
        for apt in appointments:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            doctor_user = db.query(User).filter(
                User.id == doctor.user_id
            ).first() if doctor else None

            result.append({
                "appointment_id": apt.id,
                "doctor": doctor_user.full_name if doctor_user else "غير محدد",
                "date": apt.appointment_date.strftime("%Y-%m-%d"),
                "time": apt.appointment_date.strftime("%H:%M"),
                "status": apt.status,
                "notes": apt.patient_notes or "",
            })

        return json.dumps(result, ensure_ascii=False, indent=2)
    finally:
        db.close()


# قائمة كل الـ tools عشان نبعتها للـ Agent
ALL_TOOLS = [
    get_all_doctors,
    get_doctor_info,
    check_availability,
    book_appointment,
    cancel_appointment,
    get_patient_appointments,
]