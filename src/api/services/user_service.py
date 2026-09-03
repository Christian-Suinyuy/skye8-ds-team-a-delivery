from sqlalchemy.orm import Session
from api.schema.user_schema import UserSignUp, UserLogin, AcessToken

from fastapi import status, HTTPException

from api.config.models.user import User
from api.utils.jwt_util import create_access_token
from api.utils.bcrypt import hash_password, verify_password

def handles_signUp(
        data: UserSignUp,
        db: Session
    ) -> str:
    hashed_password = hash_password(data.password)
    try:
        duplicate = db.query(User).filter(User.email == data.email).first()
        if duplicate:
            return "User with this email already exists"
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

def handle_login(
        credenetials: UserLogin,
        db: Session
):
    response = db.query(User).filter(User.email == credenetials.email).first()
    # print(response.password_hashed)
    if verify_password(credenetials.password, response.password_hashed):
        return create_access_token(str(response.id))
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )