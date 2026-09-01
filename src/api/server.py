from fastapi import FastAPI
from api.schema.user_schema import UserSignUp

app = FastAPI()

@app.get("/")
def health():
    return {"message": "server is runnig. Everything is Good"}

@app.post("/login")
def login(credential: UserSignUp):
    credentials = UserSignUp.model_dump(credential)
    print(credentials)
    return "user signed up sucessfully"