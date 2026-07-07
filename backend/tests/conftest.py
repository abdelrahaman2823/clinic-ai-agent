
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from main import app

# Database مؤقتة للتيست بس
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """إنشاء الـ tables قبل التيست ومسحها بعده"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Client جاهز لكل test"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def patient_token(client):
    """تسجيل بيشنت وإرجاع الـ token"""
    client.post("/api/v1/auth/register", json={
        "full_name": "Test Patient",
        "email": "testpatient@test.com",
        "password": "123456",
        "role": "patient",
        "phone": "01012345678"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "testpatient@test.com",
        "password": "123456"
    })
    return res.json()["access_token"]


@pytest.fixture(scope="function")
def doctor_token(client):
    """تسجيل دكتور وإرجاع الـ token"""
    client.post("/api/v1/doctors/register", json={
        "full_name": "Test Doctor",
        "email": "testdoctor@test.com",
        "password": "123456",
        "phone": "01098765432",
        "specialty": "باطنة",
        "consultation_fee": 300,
        "location": "القاهرة",
        "appointment_duration_minutes": 30,
        "working_hours": {
            "Saturday": ["09:00", "17:00"],
            "Sunday": ["09:00", "17:00"],
        }
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "testdoctor@test.com",
        "password": "123456"
    })
    return res.json()["access_token"]


@pytest.fixture(scope="function")
def secretary_token(client):
    """تسجيل سيكرتير وإرجاع الـ token"""
    client.post("/api/v1/auth/register", json={
        "full_name": "Test Secretary",
        "email": "testsecretary@test.com",
        "password": "123456",
        "role": "secretary"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "testsecretary@test.com",
        "password": "123456"
    })
    return res.json()["access_token"]