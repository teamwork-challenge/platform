#!/usr/bin/env python3
import os
import time
import subprocess
from typing import Iterator

import pytest
import requests
from requests import Response
from requests.exceptions import RequestException


PORT = 8928
BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="module", autouse=True)
def rate_limited_server() -> Iterator[None]:
    # Enable limiter with a very small window/limit to keep tests fast
    env = os.environ.copy()
    env["CH_RATE_LIMIT_ENABLED"] = "1"
    env["CH_RATE_PER_MINUTE"] = "3"  # actually per window
    env["CH_WINDOW_SECONDS"] = "1"
    # Do not change exemptions; default in middleware should be fine

    proc = subprocess.Popen([
        "uvicorn", "back.main:app", "--port", str(PORT)
    ], cwd="..", env=env)

    wait_endpoint_up(BASE_URL, 2.0)

    try:
        yield
    finally:
        proc.terminate()
        proc.wait()


def wait_endpoint_up(server_url: str, max_wait_time: float) -> None:
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(server_url, timeout=1)
            if response.status_code in (200, 307, 308):
                break
        except RequestException:
            time.sleep(0.05)


def wait_next_window(window_seconds: float = 1.0) -> None:
    # Sleep a bit over the window to ensure counters reset
    time.sleep(window_seconds + 0.25)


def _auth_headers(api_key: str = "team1") -> dict[str, str]:
    return {"X-API-Key": api_key}


def test_within_limit_allows_requests_and_sets_headers() -> None:
    wait_next_window()
    # Within the window, first 3 requests from same API key should pass
    responses: list[Response] = []
    for _ in range(3):
        r = requests.get(BASE_URL + "/auth", headers=_auth_headers(), timeout=2)
        responses.append(r)
        assert r.status_code == 200, f"Unexpected status: {r.status_code}, body={r.text}"
        # Headers set by middleware even on success
        assert r.headers.get("X-RateLimit-Limit") == "3"
        assert r.headers.get("X-RateLimit-Remaining") is not None
        assert r.headers.get("X-RateLimit-Reset") is not None


def test_exceeding_limit_returns_429_with_headers_and_body() -> None:
    wait_next_window()
    # Hit the limit quickly
    for _ in range(3):
        requests.get(BASE_URL + "/auth", headers=_auth_headers(), timeout=2)

    # Next request should be rate limited
    r = requests.get(BASE_URL + "/auth", headers=_auth_headers(), timeout=2)
    assert r.status_code == 429
    data = r.json()
    assert data.get("error") == "rate_limited"
    assert data.get("limit") == 3
    assert data.get("remaining") == 0
    assert "reset_secs" in data
    # Headers
    assert r.headers.get("Retry-After") is not None
    assert r.headers.get("X-RateLimit-Limit") == "3"
    assert r.headers.get("X-RateLimit-Remaining") == "0"
    assert r.headers.get("X-RateLimit-Reset") is not None


def test_exempt_root_not_limited() -> None:
    wait_next_window()
    # Root path "/" is exempt; should not hit 429 even after many requests
    for _ in range(10):
        r = requests.get(BASE_URL + "/", timeout=2, allow_redirects=False)
        assert r.status_code in (200, 307, 308)


def test_window_reset_allows_requests_again() -> None:
    wait_next_window()
    # Exceed the limit first
    for _ in range(4):
        requests.get(BASE_URL + "/auth", headers=_auth_headers(), timeout=2)

    # Sleep slightly over window to reset (window is 1s)
    time.sleep(1.2)

    # Should be allowed again now
    r = requests.get(BASE_URL + "/auth", headers=_auth_headers(), timeout=2)
    assert r.status_code == 200
    # And headers reflect remaining below limit
    assert r.headers.get("X-RateLimit-Limit") == "3"
    remaining = r.headers.get("X-RateLimit-Remaining")
    assert remaining is not None and int(remaining) >= 1
