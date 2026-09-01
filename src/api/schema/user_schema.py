from pydantic import BaseModel

class UserSignUp(BaseModel):
    email: str
    password: str
    confirm_pass: str

class UserLogin(BaseModel):
    email: str
    password: str

class AcessToken(BaseModel):
    access_token: str
    token_type: str