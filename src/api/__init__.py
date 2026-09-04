import uvicorn


def main() -> None:
    uvicorn.run("api.server:app", host="0.0.0.0", port=8005, reload=True)
