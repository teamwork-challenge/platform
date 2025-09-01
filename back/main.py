import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from mangum import Mangum
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE: bool = True
except Exception:
    SLOWAPI_AVAILABLE = False
# Routers split by domain
from back.api_teams import router as team_router
from back.api_challenges import router as challenges_router
from back.api_tasks import router as tasks_router
from back.api_boards import router as boards_router
from back.api_task_gen import router as task_gen_router


app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0",
              debug=True)

# Global rate limiting using SlowAPI (optional)
if SLOWAPI_AVAILABLE:
    from typing import cast
    from starlette.requests import Request
    from starlette.responses import Response

    _rate = os.getenv("CHALLENGE_RATE_LIMIT", "1000/minute")
    limiter = Limiter(key_func=get_remote_address, default_limits=[_rate])
    app.state.limiter = limiter

    # Wrap SlowAPI handler to satisfy Starlette's exception handler type signature
    def _rate_limit_wrapper(request: Request, exc: Exception) -> Response:
        return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))

    app.add_exception_handler(RateLimitExceeded, _rate_limit_wrapper)
    app.add_middleware(SlowAPIMiddleware)

# Include split routers
app.include_router(team_router)
app.include_router(challenges_router)
app.include_router(tasks_router)
app.include_router(boards_router)


# Hide task generators from OpenAPI
app.include_router(task_gen_router, include_in_schema=False)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")


handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    uvicorn.run(
        "back.main:app",
        reload=True,
        reload_dirs=[".", "../api_models"],
        port=8918,
    )
