import time

from fastapi import Request


async def request_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    print(f"{request.method} {request.url.path} " f"{response.status_code} " f"{duration:.3f}s")
    return response
