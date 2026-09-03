from fastapi import FastAPI, Depends, Security, UploadFile, File, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from api.schema.user_schema import UserSignUp, UserLogin
from api.schema.model import BatchPredictionResponse, PredictionRequest, PredictionResponse
from api.services.user_service import handles_signUp, handle_login
from api.config.database import get_db
from api.utils.load_models import load_models
from api.middleware.middleware import request_logger
from api.middleware.auth import get_current_user

from api.services.model_service import (
    BatchPredictionError,
    get_prediction as model_prediction,
    predict_batch_csv,
)

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
    Depends(get_current_user)
])


def health():
    return {"message": "server is runnig. Everything is Good"}

@app.post("/api/v1/predict", dependencies= [
    Depends(get_current_user)
])
def get_prediction(features: PredictionRequest) -> PredictionResponse:
    return model_prediction(features)


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    file: UploadFile = File(...),
    _: str = Depends(get_current_user),
) -> BatchPredictionResponse:
    try:
        return predict_batch_csv(await file.read(), file.content_type)
    except BatchPredictionError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error