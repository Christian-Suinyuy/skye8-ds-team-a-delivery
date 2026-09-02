from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from api.schema.user_schema import UserSignUp, UserLogin
from api.user_service import handles_signUp, handle_login
from api.config.database import get_db
from api.utils.load_models import load_models
from api.middleware import request_logger

app = FastAPI()

load_models()
app.middleware("http")(request_logger)

@app.get("/")
def health():
    return {"message": "server is runnig. Everything is Good"}

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
    
    