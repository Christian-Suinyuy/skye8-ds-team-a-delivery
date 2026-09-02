from pydantic import BaseModel, EmailStr

class UserSignUp(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class AcessToken(BaseModel):
    access_token: str
    token_type: str