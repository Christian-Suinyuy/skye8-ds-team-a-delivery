from fastapi import FastAPI
from api.schema.user_schema import UserSignUp
from api.user_service import handleSignUp

app = FastAPI()

@app.get("/")
def health():
    return {"message": "server is runnig. Everything is Good"}

@app.post("/login")
def login(credentials: UserSignUp):
    token = handleSignUp(credentials)
    return {"access_token": token, "token_type": "bearer"}