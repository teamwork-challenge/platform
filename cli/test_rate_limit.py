#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from typing import Iterator

import pytest
import requests
from requests import Response


# Skip these tests gracefully if slowapi is not available in the environment
from importlib.util import find_spec
SLOWAPI_AVAILABLE = find_spec("slowapi") is not None


RATE_LIMIT_PORT = 8920
BASE_URL = f"http://127.0.0.1:{RATE_LIMIT_PORT}"


def _wait_endpoint_up(url: str, timeout: float = 3.0) -> None:
    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout:
        try:
            # /docs should return 200 when FastAPI is up
            r = requests.get(url + "/docs", timeout=1)
            if 200 <= r.status_code < 500:
                return
        except Exception as e:  # pragma: no cover - just waiting for server
            last_err = e
            time.sleep(0.1)
    if last_err:
        raise last_err
    raise RuntimeError("Server did not start in time")


@pytest.fixture()
def rate_limited_server() -> Iterator[None]:
    # Ensure child server sees a very small limit to trip quickly
    env = os.environ.copy()
    env["CHALLENGE_RATE_LIMIT"] = "3/second"

    # Launch a dedicated uvicorn instance for this test module
    # Tests run from cli\, so the backend lives one directory up
    proc = subprocess.Popen([
        "uvicorn", "back.main:app", "--port", str(RATE_LIMIT_PORT)
    ], cwd="..", env=env)

    try:
        _wait_endpoint_up(BASE_URL, timeout=5.0)
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            proc.kill()


@pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi is not installed; rate limit middleware disabled")
def test_rate_limit_exceeded(rate_limited_server: None) -> None:
    # Make 5 quick requests to '/' without following redirects
    # With 3/second limit: first 3 should be allowed (200/307), next should be 429
    responses: list[Response] = []
    for _ in range(5):
        responses.append(requests.get(BASE_URL + "/", allow_redirects=False, timeout=2))

    # First three are not 429
    assert all(resp.status_code != 429 for resp in responses[:3])

    # Fourth and fifth should be limited
    assert responses[3].status_code == 429
    assert responses[4].status_code == 429


@pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi is not installed; rate limit middleware disabled")
def test_rate_limit_window_resets(rate_limited_server: None) -> None:
    # Trip the limiter first
    for _ in range(5):
        _ = requests.get(BASE_URL + "/", allow_redirects=False, timeout=2)

    # Wait for the 1-second window to reset
    time.sleep(1.2)

    # Should be allowed again for first three
    for i in range(3):
        resp = requests.get(BASE_URL + "/", allow_redirects=False, timeout=2)
        assert resp.status_code != 429, f"Unexpected 429 on request {i+1} after window reset"
