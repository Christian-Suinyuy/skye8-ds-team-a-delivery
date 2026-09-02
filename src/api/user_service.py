from dotenv import load_dotenv
import os

from sqlalchemy.orm import Session
from fastapi import Depends

from pwdlib import PasswordHash
from api.config.database import get_db
from api.schema.user_schema import UserSignUp, UserLogin, AcessToken
from datetime import datetime, timedelta, timezone
from api.config.models.user import User
import jwt

load_dotenv()
secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGORITHM")

password_hash = PasswordHash.recommended()

def hash_password(password:str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes = 30)

    payload = {
        "sub": user_id,
        "exp": expires
    }

    return jwt.encode(payload, secret_key, algorithm = algorithm)

def handleSignUp(
        data: UserSignUp,
        db: Session = Depends(get_db)
    ) -> str:
    hashed_password = hash_password(data.password)
    try:
        user = User(
            email=data.email,
            password_hashed=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return create_access_token(str(user.id))
    except Exception as e:
        db.rollback()
        raise e