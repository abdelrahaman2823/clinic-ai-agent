
def test_register_patient(client):
    """تسجيل بيشنت جديد"""
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Ahmed Ali",
        "email": "ahmed@test.com",
        "password": "123456",
        "role": "patient"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "ahmed@test.com"
    assert data["role"] == "patient"


def test_register_duplicate_email(client):
    """منع تكرار الإيميل"""
    client.post("/api/v1/auth/register", json={
        "full_name": "User One",
        "email": "duplicate@test.com",
        "password": "123456",
        "role": "patient"
    })
    res = client.post("/api/v1/auth/register", json={
        "full_name": "User Two",
        "email": "duplicate@test.com",
        "password": "123456",
        "role": "patient"
    })
    assert res.status_code == 400


def test_login_success(client):
    """تسجيل دخول صح"""
    client.post("/api/v1/auth/register", json={
        "full_name": "Login Test",
        "email": "logintest@test.com",
        "password": "123456",
        "role": "patient"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "logintest@test.com",
        "password": "123456"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    """رفض باسورد غلط"""
    client.post("/api/v1/auth/register", json={
        "full_name": "Wrong Pass",
        "email": "wrongpass@test.com",
        "password": "123456",
        "role": "patient"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401


def test_protected_route_without_token(client):
    """رفض الوصول بدون token"""
    res = client.get("/api/v1/appointments/")
    assert res.status_code == 403


def test_protected_route_with_token(client, patient_token):
    """السماح بالوصول بـ token صح"""
    res = client.get(
        "/api/v1/appointments/my",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 200