#!/usr/bin/env python3
from typer.testing import CliRunner, Result

from main import app
import pytest
import subprocess
import time
import os

@pytest.fixture(scope="session", autouse=True)
def start_server():
    proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8888"], cwd="../back")
    os.environ["CHALLENGE_API_URL"] = "http://127.0.0.1:8888" # make CLI use the same port
    time.sleep(1.5)
    yield
    proc.terminate()
    proc.wait()

runner = CliRunner()

def test_login_ok():
    login_team1()

def test_login_fail():
    result = runner.invoke(app, ["login", "team1123123"])
    assert result.exit_code != 0

def test_team_show_ok():
    login_team1()
    result = run_ok("team", "show")
    assert "Team ID: 1" in result.output

def test_challenge_show_ok():
    login_team1()
    result = run_ok("show", "-c", "1")
    assert "Challenge" in result.output


def login_team1() -> Result:
    return run_ok("login", "team1")

def login_team2() -> Result:
    return run_ok("login", "team2")

def run_ok(*args: str) -> Result:
    result = runner.invoke(app, list(args))
    print(f"Output: {result.output}")
    if result.exit_code != 0:
        print(f"Command failed with exit code {result.exit_code}")
        print(f"Error Output: {result.stderr}")
        assert False, f"Command failed with exit code {result.exit_code}"
    return result
