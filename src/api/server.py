from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    return {"message": "server is runnig. Everything is Good"}