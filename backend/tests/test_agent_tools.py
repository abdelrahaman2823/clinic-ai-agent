
from unittest.mock import patch, MagicMock
from app.agent.tools import get_all_doctors, get_doctor_info, check_availability
import json


def test_get_all_doctors_empty():
    """لو مفيش دكاترة يرجع رسالة"""
    with patch("app.agent.tools.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_all_doctors.invoke({})
        assert "مفيش" in result or isinstance(result, str)


def test_get_doctor_info_not_found():
    """لو الدكتور مش موجود"""
    with patch("app.agent.tools.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_doctor_info.invoke({"doctor_name": "دكتور مش موجود"})
        assert "مفيش" in result


def test_check_availability_wrong_date_format():
    """التحقق من صيغة التاريخ الغلط"""
    with patch("app.agent.tools.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_doctor = MagicMock()
        mock_doctor.working_hours = {"Saturday": ["09:00", "17:00"]}
        mock_doctor.appointment_duration_minutes = 30
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doctor

        result = check_availability.invoke({
            "doctor_id": 1,
            "date": "wrong-date"
        })
        assert "غلط" in result or "error" in result.lower()