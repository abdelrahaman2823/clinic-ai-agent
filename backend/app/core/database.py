# backend/app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # يتحقق من الـ connection قبل الاستخدام
    pool_size=10,             # عدد connections في الـ pool
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency — بتستخدمها في كل route تحتاج DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()