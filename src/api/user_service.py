from dotenv import load_dotenv
import os

from pwdlib import PasswordHash
from api.schema.user_schema import UserSignUp, UserLogin, AcessToken
from datetime import datetime, timedelta, timezone
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

def handleSignUp(data: UserSignUp) -> dict:
    hashed_password = hash_password(data.password)
    return {
        "email": data.email,
        "password": hashed_password
    }