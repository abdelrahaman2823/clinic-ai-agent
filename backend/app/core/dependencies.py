from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """الـ dependency ده بتحطه في أي route تحتاج login"""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token غير صالح أو منتهي"
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="المستخدم مش موجود")

    return user


def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    """بس الدكتور يعدي"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="مش مسموح — دكاترة بس")
    return current_user


def require_secretary(current_user: User = Depends(get_current_user)) -> User:
    """السكرتير أو الدكتور"""
    if current_user.role not in [UserRole.secretary, UserRole.doctor]:
        raise HTTPException(status_code=403, detail="مش مسموح")
    return current_user