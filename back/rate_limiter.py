import os
import time
import math
import threading
from typing import Dict, Tuple, Iterable, Any, cast

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class _InMemoryCounter:
    """Simple fixed-window counter store for a single-process app.

    Key -> (window_start_epoch_seconds, count)
    """

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[float, int]] = {}
        self._lock = threading.Lock()

    def inc(self, key: str, window_seconds: int, now: float) -> Tuple[int, int, float]:
        """Increment counter for the current window and return (count, limit_remaining, reset_secs).

        Note: limit_remaining to be calculated by caller once limit is known; we return:
        - count in this window after increment
        - window_epoch_start as int
        - reset_secs (float seconds until window end)
        """
        window_start = math.floor(now / window_seconds) * window_seconds
        with self._lock:
            entry = self._data.get(key)
            if entry is None or entry[0] != window_start:
                # New window
                self._data[key] = (window_start, 1)
                count = 1
            else:
                count = entry[1] + 1
                self._data[key] = (entry[0], count)
        reset_secs = (window_start + window_seconds) - now
        return count, int(window_start), max(0.0, reset_secs)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter with per-identity keys.

    Identity: X-API-Key header if present; else client IP.
    Exemptions: configurable paths (prefix match for /docs and /redoc), always exempt OPTIONS.
    Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset; 429 includes Retry-After.
    """

    def __init__(
        self,
        app: FastAPI,
        *,
        limit_per_window: int = 60,
        window_seconds: int = 60,
        exempt_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limit_per_window = max(1, int(limit_per_window))
        self.window_seconds = max(1, int(window_seconds))
        self.exempt_paths = list(exempt_paths or ["/", "/docs", "/openapi.json", "/redoc"])
        self._store = _InMemoryCounter()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exempt methods and paths
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in self.exempt_paths):
            return await call_next(request)

        # Build identity key: prefer API key, else client IP
        api_key = request.headers.get("X-API-Key")
        if api_key:
            identity = f"api:{api_key}"
            scope = "api_key"
        else:
            client_host = request.client.host if request.client else "unknown"
            identity = f"ip:{client_host}"
            scope = "ip"

        now = time.time()
        count, _window_start, reset_secs = self._store.inc(identity, self.window_seconds, now)
        remaining = max(0, self.limit_per_window - count)
        reset_secs_int = int(math.ceil(reset_secs))

        if count > self.limit_per_window:
            # Too many requests
            body = {
                "error": "rate_limited",
                "message": f"Rate limit exceeded: {self.limit_per_window}/{self.window_seconds}s for {scope}",
                "limit": self.limit_per_window,
                "remaining": 0,
                "reset_secs": reset_secs_int,
                "scope": scope,
                "endpoint": path,
            }
            return JSONResponse(
                status_code=429,
                content=body,
                headers={
                    "Retry-After": str(max(1, reset_secs_int)),
                    "X-RateLimit-Limit": str(self.limit_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_secs_int),
                },
            )

        # Allowed -> proceed and annotate response headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_secs_int)
        return response


def _env_flag(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y")


def setup_rate_limiter(app: FastAPI) -> None:
    if not _env_flag("CH_RATE_LIMIT_ENABLED", default=False):
        return

    kwargs: dict[str, Any] = {}

    if "CH_RATE_PER_MINUTE" in os.environ:
        try:
            kwargs["limit_per_window"] = int(os.environ["CH_RATE_PER_MINUTE"])
        except ValueError:
            pass

    if "CH_WINDOW_SECONDS" in os.environ:
        try:
            kwargs["window_seconds"] = int(os.environ["CH_WINDOW_SECONDS"])
        except ValueError:
            pass

    exempt_env = os.environ.get("CH_EXEMPT_PATHS")
    if exempt_env:
        kwargs["exempt_paths"] = [p.strip() for p in exempt_env.split(",") if p.strip()]

    app.add_middleware(
        cast(Any, RateLimiterMiddleware),
        **kwargs,
    )