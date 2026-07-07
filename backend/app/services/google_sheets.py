
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.core.config import settings
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# أسماء الـ sheets جوا الـ spreadsheet
SHEET_APPOINTMENTS = "Appointments"
SHEET_DOCTORS      = "Doctors"
SHEET_PATIENTS     = "Patients"


class GoogleSheetsService:
    def __init__(self):
        self._service = None

    def _get_service(self):
        """Lazy init — مش بيتوصل إلا لما يحتاج"""
        if self._service:
            return self._service
        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=SCOPES
            )
            self._service = build("sheets", "v4", credentials=credentials)
        except Exception as e:
            logger.warning(f"Google Sheets not configured: {e}")
            self._service = None
        return self._service

    def _sheets(self):
        svc = self._get_service()
        if not svc:
            return None
        return svc.spreadsheets()

    # ══ Setup ══

    def setup_all_sheets(self):
        """إعداد كل الـ sheets لأول مرة"""
        self._setup_appointments_sheet()
        self._setup_doctors_sheet()
        self._setup_patients_sheet()

    def _setup_appointments_sheet(self):
        sheets = self._sheets()
        if not sheets:
            return
        headers = [[
            "ID", "اسم المريض", "تليفون المريض", "إيميل المريض",
            "الدكتور", "التخصص", "التاريخ", "الوقت",
            "الحالة", "ملاحظات المريض", "ملاحظات الدكتور", "تاريخ الإنشاء"
        ]]
        try:
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_APPOINTMENTS}!A1:L1",
                valueInputOption="USER_ENTERED",
                body={"values": headers}
            ).execute()
        except Exception as e:
            logger.error(f"Setup appointments sheet error: {e}")

    def _setup_doctors_sheet(self):
        sheets = self._sheets()
        if not sheets:
            return
        headers = [["ID", "الاسم", "التخصص", "السعر", "التليفون", "العنوان"]]
        try:
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_DOCTORS}!A1:F1",
                valueInputOption="USER_ENTERED",
                body={"values": headers}
            ).execute()
        except Exception as e:
            logger.error(f"Setup doctors sheet error: {e}")

    def _setup_patients_sheet(self):
        sheets = self._sheets()
        if not sheets:
            return
        headers = [["ID", "الاسم", "التليفون", "الإيميل", "تاريخ التسجيل"]]
        try:
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_PATIENTS}!A1:E1",
                valueInputOption="USER_ENTERED",
                body={"values": headers}
            ).execute()
        except Exception as e:
            logger.error(f"Setup patients sheet error: {e}")

    # ══ Appointments ══

    def append_appointment(self, data: dict) -> int:
        sheets = self._sheets()
        if not sheets:
            return 0
        values = [[
            data.get("id", ""),
            data.get("patient_name", ""),
            data.get("patient_phone", ""),
            data.get("patient_email", ""),
            data.get("doctor_name", ""),
            data.get("doctor_specialty", ""),
            data.get("appointment_date", ""),
            data.get("appointment_time", ""),
            data.get("status", "pending"),
            data.get("patient_notes", ""),
            data.get("doctor_notes", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ]]
        try:
            result = sheets.values().append(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_APPOINTMENTS}!A:L",
                valueInputOption="USER_ENTERED",
                body={"values": values}
            ).execute()
            updated_range = result.get("updates", {}).get("updatedRange", "")
            if updated_range:
                row_num = int(updated_range.split(":")[0].split("A")[1])
                return row_num
        except Exception as e:
            logger.error(f"Append appointment error: {e}")
        return 0

    def update_appointment_status(self, row_id: int, status: str):
        sheets = self._sheets()
        if not sheets or not row_id:
            return
        try:
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_APPOINTMENTS}!I{row_id}",
                valueInputOption="USER_ENTERED",
                body={"values": [[status]]}
            ).execute()
        except Exception as e:
            logger.error(f"Update status error: {e}")

    def sync_all_appointments(self, appointments: List[dict]):
        """مزامنة كل المواعيد من الـ DB للـ Sheet"""
        sheets = self._sheets()
        if not sheets:
            return
        self._setup_appointments_sheet()
        values = []
        for apt in appointments:
            values.append([
                apt.get("id", ""),
                apt.get("patient_name", ""),
                apt.get("patient_phone", ""),
                apt.get("patient_email", ""),
                apt.get("doctor_name", ""),
                apt.get("doctor_specialty", ""),
                apt.get("appointment_date", ""),
                apt.get("appointment_time", ""),
                apt.get("status", ""),
                apt.get("patient_notes", ""),
                apt.get("doctor_notes", ""),
                apt.get("created_at", ""),
            ])
        if not values:
            return
        try:
            # امسح الداتا القديمة وحط الجديدة
            sheets.values().clear(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_APPOINTMENTS}!A2:L1000",
            ).execute()
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_APPOINTMENTS}!A2",
                valueInputOption="USER_ENTERED",
                body={"values": values}
            ).execute()
        except Exception as e:
            logger.error(f"Sync all appointments error: {e}")

    # ══ Doctors ══

    def sync_doctors(self, doctors: List[dict]):
        sheets = self._sheets()
        if not sheets:
            return
        self._setup_doctors_sheet()
        values = [[
            d.get("id"), d.get("name"), d.get("specialty"),
            d.get("consultation_fee"), d.get("phone"), d.get("location")
        ] for d in doctors]
        if not values:
            return
        try:
            sheets.values().clear(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_DOCTORS}!A2:F1000",
            ).execute()
            sheets.values().update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_DOCTORS}!A2",
                valueInputOption="USER_ENTERED",
                body={"values": values}
            ).execute()
        except Exception as e:
            logger.error(f"Sync doctors error: {e}")

    # ══ Patients ══

    def append_patient(self, data: dict):
        sheets = self._sheets()
        if not sheets:
            return
        values = [[
            data.get("id"), data.get("full_name"),
            data.get("phone", ""), data.get("email", ""),
            datetime.now().strftime("%Y-%m-%d"),
        ]]
        try:
            sheets.values().append(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{SHEET_PATIENTS}!A:E",
                valueInputOption="USER_ENTERED",
                body={"values": values}
            ).execute()
        except Exception as e:
            logger.error(f"Append patient error: {e}")


sheets_service = GoogleSheetsService()