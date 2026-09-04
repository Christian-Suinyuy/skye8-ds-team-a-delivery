import json
import logging
import sys
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request

logger = logging.getLogger("api.requests")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)


async def request_logger(request: Request, call_next):
    request_id = str(uuid4())
    started_at = datetime.now(UTC)
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed %s",
            json.dumps(
                {
                    "request_id": request_id,
                    "timestamp": started_at.isoformat(),
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
                sort_keys=True,
            ),
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    log_data = {
        "request_id": request_id,
        "timestamp": started_at.isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }

    if response.status_code >= 400:
        response_body = getattr(response, "body", b"")
        if response_body:
            try:
                log_data["error"] = json.loads(response_body)
            except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
                log_data["error"] = response_body.decode("utf-8", errors="replace")
        logger.warning("request_error %s", json.dumps(log_data, sort_keys=True, default=str))
    else:
        logger.info("request_complete %s", json.dumps(log_data, sort_keys=True))

    response.headers["X-Request-ID"] = request_id
    return response
