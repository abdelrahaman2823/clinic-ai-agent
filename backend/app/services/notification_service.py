
from datetime import datetime


class NotificationService:
    """
    Notification service — دلوقتي بيعمل log بس
    لو عايز SMS حقيقي تقدر تضيف Twilio أو Vonage لاحقاً
    """

    def send_booking_confirmation(
        self,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        appointment_id: int,
    ):
        message = (
            f"تم تأكيد حجزك يا {patient_name}!\n"
            f"الدكتور: {doctor_name}\n"
            f"التاريخ: {appointment_date} الساعة {appointment_time}\n"
            f"رقم الحجز: #{appointment_id}"
        )
        print(f"[NOTIFICATION] To: {patient_phone}\n{message}\n")
        return True

    def send_cancellation_notice(
        self,
        patient_name: str,
        patient_phone: str,
        appointment_id: int,
    ):
        message = (
            f"تم إلغاء الحجز #{appointment_id} يا {patient_name}.\n"
            f"لو محتاج تحجز تاني، كلمنا في أي وقت."
        )
        print(f"[NOTIFICATION] To: {patient_phone}\n{message}\n")
        return True

    def send_reminder(
        self,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
    ):
        message = (
            f"تذكير: عندك موعد بكره يا {patient_name}\n"
            f"الدكتور: {doctor_name}\n"
            f"الساعة: {appointment_time}"
        )
        print(f"[NOTIFICATION] To: {patient_phone}\n{message}\n")
        return True


notification_service = NotificationService()