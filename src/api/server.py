from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from api.schema.user_schema import UserSignUp
from api.user_service import handleSignUp
from api.config.database import get_db
from api.config.load_models import load_models

app = FastAPI()

load_models()

@app.get("/")
def health():
    return {"message": "server is runnig. Everything is Good"}

@app.post("/signup")
def login(
    credentials: UserSignUp,
    db: Session = Depends(get_db)
):
    token = handleSignUp(credentials, db)
    return {"access_token": token, "token_type": "bearer"}