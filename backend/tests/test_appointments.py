
def test_get_all_doctors(client, doctor_token):
    """جلب قائمة الدكاترة"""
    res = client.get("/api/v1/doctors/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


def test_get_today_appointments(client, secretary_token):
    """جلب مواعيد النهارده"""
    res = client.get(
        "/api/v1/appointments/today",
        headers={"Authorization": f"Bearer {secretary_token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_stats(client, secretary_token):
    """جلب الإحصائيات"""
    res = client.get(
        "/api/v1/appointments/stats",
        headers={"Authorization": f"Bearer {secretary_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "today" in data
    assert "pending" in data
    assert "confirmed" in data
    assert "cancelled" in data


def test_get_my_appointments(client, patient_token):
    """البيشنت يشوف مواعيده"""
    res = client.get(
        "/api/v1/appointments/my",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_patient_cannot_access_all_appointments(client, patient_token):
    """البيشنت مش يقدر يشوف كل المواعيد"""
    res = client.get(
        "/api/v1/appointments/",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 403


def test_get_all_patients(client, secretary_token):
    """السيكرتير يشوف كل المرضى"""
    res = client.get(
        "/api/v1/patients/",
        headers={"Authorization": f"Bearer {secretary_token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_search_patients(client, secretary_token):
    """البحث في المرضى"""
    res = client.get(
        "/api/v1/patients/?search=Test",
        headers={"Authorization": f"Bearer {secretary_token}"}
    )
    assert res.status_code == 200


def test_health_check(client):
    """تأكد إن الـ API شغال"""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"