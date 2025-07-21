#!/usr/bin/env python3
from typer.testing import CliRunner, Result
from pathlib import Path
import tempfile
import os.path

from main import app
import pytest
import subprocess
import time
import os
import requests
from requests.exceptions import RequestException


@pytest.fixture(scope="session", autouse=True)
def start_server():
    proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8888"], cwd="../back")
    os.environ["CHALLENGE_API_URL"] = "http://127.0.0.1:8888" # make CLI use the same port

    # Wait for the backend to start responding, with a maximum timeout of 10 seconds
    start_time = time.time()
    max_wait_time = 10.0
    server_url = "http://127.0.0.1:8888"

    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(server_url, timeout=1)
            if response.status_code == 200 or response.status_code == 404:
                # Server is responding (200 OK or 404 Not Found are both valid responses)
                break
        except RequestException:
            # Server not responding yet, wait a bit and retry
            time.sleep(0.5)

    yield
    proc.terminate()
    proc.wait()

runner = CliRunner()

# Challenge App Tests
def test_login_ok():
    result = login_team1()
    assert "Successfully logged in" in result.output

def test_login_fail():
    result = runner.invoke(app, ["login", "team1123123"])
    assert result.exit_code != 0

def test_logout():
    login_team1()
    result = run_ok("logout")
    assert "Successfully logged out" in result.output

def test_challenge_show_ok():
    login_team1()
    result = run_ok("show", "-c", "1")
    assert "Challenge" in result.output

def test_challenge_update():
    login_admin()
    result = run_ok("update", "-c", "1", "-t", "Updated Challenge Title")
    assert "Challenge updated successfully" in result.output

def test_challenge_delete():
    login_admin()
    # Use --yes to skip confirmation prompt
    result = run_ok("delete", "-c", "1", "--yes")
    assert "marked as deleted successfully" in result.output
    # result = run_ok("update", "-c", "1", "--deleted")
    # assert "marked as not deleted successfully" in result.output

# Team App Tests
def test_team_show_ok():
    login_team1()
    result = run_ok("team", "show")
    assert "Team ID: 1" in result.output

# Round App Tests
def test_round_show():
    login_team1()
    result = run_ok("round", "show", "-r", "1")
    assert "Round 1 Information" in result.output

def test_round_list():
    login_team1()
    result = run_ok("round", "list")
    assert "Rounds" in result.output

def test_round_publish():
    login_team1()
    result = run_ok("round", "publish", "1")
    assert "Round published" in result.output

def test_round_update():
    login_team1()
    result = run_ok("round", "update", "-r", "1", "--status", "active")
    assert "Round 1 updated successfully" in result.output

def test_round_delete():
    login_team1()
    # Use --yes to skip confirmation prompt
    result = run_ok("round", "delete", "-r", "1", "--yes")
    assert "Round 1 deleted successfully" in result.output

# Task App Tests
def test_task_claim():
    login_team1()
    result = run_ok("task", "claim")
    assert "Successfully claimed task" in result.output

def test_task_show():
    login_team1()
    # First claim a task to get a task ID
    claim_result = run_ok("task", "claim")
    task_id = extract_task_id(claim_result.output)

    result = run_ok("task", "task_show", task_id)
    assert f"Task {task_id} Information" in result.output

def test_task_show_input():
    login_team1()
    # First claim a task to get a task ID
    claim_result = run_ok("task", "claim")
    task_id = extract_task_id(claim_result.output)

    result = run_ok("task", "show-input", task_id)
    assert result.exit_code == 0

def test_task_submit():
    login_team1()
    # First claim a task to get a task ID
    claim_result = run_ok("task", "claim")
    task_id = extract_task_id(claim_result.output)

    # Create a temporary file with an answer
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test answer")
        temp_file = f.name

    try:
        result = run_ok("task", "submit", task_id, "--file", temp_file)
        assert "Successfully submitted answer" in result.output
    finally:
        # Clean up the temporary file
        os.unlink(temp_file)

def test_task_list():
    login_team1()
    result = run_ok("task", "list")
    assert "Tasks" in result.output

# Board App Tests
def test_board_dashboard():
    login_team1()
    result = run_ok("board", "dashboard")
    assert "Dashboard for Round" in result.output

def test_board_leaderboard():
    login_team1()
    result = run_ok("board", "leaderboard")
    assert "Leaderboard for Round" in result.output

def login_admin() -> Result:
    return run_ok("login", "admin1")

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

def extract_task_id(output: str) -> str:
    """Extract task ID from the output of the claim command."""
    for line in output.splitlines():
        if "Task ID:" in line:
            return line.split("Task ID:")[1].strip()
    return "1"  # Fallback to a default ID if extraction fails
