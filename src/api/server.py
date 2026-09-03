from fastapi import FastAPI, Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from api.schema.user_schema import UserSignUp, UserLogin
from api.services.user_service import handles_signUp, handle_login
from api.config.database import get_db
from api.utils.load_models import load_models
from api.middleware.middleware import request_logger
from api.middleware.auth import auth_middleware

app = FastAPI()



load_models()
app.middleware("http")(request_logger)



@app.post("/signup")
def signUp(
    credentials: UserSignUp,
    db: Session = Depends(get_db)
):
    token = handles_signUp(credentials, db)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/signin")
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    token = handle_login(credentials, db)

    return {"access_token": token, "token_type": "bearer"}

@app.get("/", dependencies = [
    Depends(auth_middleware)
])
def health():
    return {"message": "server is runnig. Everything is Good"}

    