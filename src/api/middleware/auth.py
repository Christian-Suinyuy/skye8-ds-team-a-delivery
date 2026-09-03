from fastapi import HTTPException, status, Request
from jwt import PyJWTError
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import dotenv
import os

dotenv.load_dotenv()
secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGORITHM")


async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "could not validate credentials",
            headers= {"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(token, secret_key, algorithms = algorithm)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "could not validate credentials",
                headers= {"WWW-Authenticate": "Bearer"}
            )

    except PyJWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "could not validate credentials",
            headers= {"WWW-Authenticate": "Bearer"}
        )

    response = await call_next(request)
    return response