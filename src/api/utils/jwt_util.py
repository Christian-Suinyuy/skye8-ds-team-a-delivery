import os
from datetime import UTC, datetime, timedelta

import dotenv
import jwt

dotenv.load_dotenv()
secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGORITHM")


def create_access_token(user_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=30)

    payload = {"sub": user_id, "exp": expires}

    return jwt.encode(payload, secret_key, algorithm=algorithm)
