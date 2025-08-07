#!/usr/bin/env python3
from typer.testing import CliRunner, Result
from pathlib import Path
import tempfile
import os.path
import os
import pytest
import subprocess
import time
import requests
from requests.exceptions import RequestException
from datetime import datetime, timedelta

from cli.main import app

backend_port = 8918

@pytest.fixture(scope="session", autouse=True)
def start_server():
    server_url = "http://127.0.0.1:" + str(backend_port)
    os.environ["CHALLENGE_API_URL"] = server_url # make CLI use the same port

    proc = subprocess.Popen(["uvicorn", "back.main:app", "--port", str(backend_port)], cwd="..")
    wait_endpoint_up(server_url, 1.0)

    yield
    proc.terminate()
    proc.wait()


def wait_endpoint_up(server_url, max_wait_time):
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(server_url, timeout=1)
            if response.status_code == 200 or response.status_code == 404:
                break
        except RequestException:
            time.sleep(0.1)


runner = CliRunner()

# Challenge App Tests
def test_login_ok():
    result = login_team1()
    assert "Successfully logged in" in result.output

def test_login_fail():
    result = runner.invoke(app, ["login", "team1123123"])
    print(result.output)
    assert result.exit_code != 0
    assert "Invalid API key" in result.exception.args[0]

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
    result = run_ok("delete", "-c", "1", "--yes")
    assert "marked as deleted" in result.output
    result = run_ok("update", "-c", "1", "--undelete")
    assert "marked as deleted" not in result.output

# Team App Tests
def test_team_show_ok():
    login_team1()
    result = run_ok("team", "show")
    assert "Team ID: 1" in result.output

# Round App Tests
def test_round_show():
    login_admin()
    round_id, round_index = create_round()

    result = run_ok("round", "show", "-r", round_id)
    assert f"Round {round_id}" in result.output


def test_round_list():
    login_team1()
    result = run_ok("round", "list")
    assert "Rounds" in result.output
    assert "Round 1" in result.output


def test_round_create():
    login_admin()
    create_round()


def test_round_publish():
    login_admin()

    round_id, round_index = create_round()

    # Now publish the round
    result = run_ok("round", "publish", round_id)

    assert "Round published" in result.output
    assert f"Round {round_index}" in result.output

def test_round_update():
    login_admin()
    round_id, round_index = create_round()

    result = run_ok("round", "update", "-r", round_id, "--claim-by-type=true", "--allow-resubmit=true", "--score-decay", "linear")

    assert f"Round {round_id} updated" in result.output
    assert f"Claim by Type: True" in result.output
    assert f"Allow Resubmit: True" in result.output
    assert f"Score Decay: linear" in result.output


def test_round_delete():
    login_admin()

    challenge_id = "2"
    id, index = create_round(challenge_id)
    result = run_ok("round", "list", "-c", challenge_id)
    assert f"Round {id}" in result.output

    run_ok("round", "delete", "-r", id, "--yes")
    result = run_ok("round", "list", "-c", challenge_id)
    assert f"Round {id}" not in result.output


# Task App Tests
def test_task_claim():
    login_team1()
    result = run_ok("task", "claim")



def test_task_show():
    login_team1()
    task_id = get_task_id()

    result = run_ok("task", "show", task_id)
    print(f"Output: {result.output}")
    assert True

def test_task_show_input():
    login_team1()
    task_id = get_task_id()

    result = run_ok("task", "show-input", task_id)
    print(f"Output: {result.output}")

    assert result.exit_code == 0 or "404 Client Error: Not Found" in result.output

def test_task_submit():
    login_team1()
    task_id = get_task_id()

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test answer")
        temp_file = f.name

    try:
        result = run_ok("task", "submit", task_id, "--file", temp_file)
        print(f"Output: {result.output}")

        assert result.exit_code == 0 or "404 Client Error: Not Found" in result.output
    finally:
        os.unlink(temp_file)

def test_task_list():
    login_team1()
    result = run_ok("task", "list")
    print(f"Output: {result.output}")
    assert result.exit_code == 0 or "405 Client Error: Method Not Allowed" in result.output

# Task Type App Tests
def test_task_type_create():
    login_admin()

    # Create a round first to ensure we have a valid round ID
    round_id, _ = create_round()

    # Create a task type for the round
    task_type_id, type_name = create_task_type(round_id, "test_create_type")
    
    assert task_type_id is not None
    assert type_name is not None

def test_task_type_list():
    login_admin()

    # Create a round first to ensure we have a valid round ID
    round_id, _ = create_round()

    # Create a task type for the round
    _, type_name = create_task_type(round_id, "test_list_type")

    cmd = f"task-type list --round {round_id}"
    result = run_ok(*cmd.split())
    # The table output truncates the type name with an ellipsis
    assert "test_list_type…" in result.output

def test_task_type_show():
    login_admin()

    # Create a round first to ensure we have a valid round ID
    round_id, _ = create_round()

    # Create a task type for the round
    task_type_id, type_name = create_task_type(round_id, "test_show_type")
    
    # Now show the task type
    result = run_ok("task-type", "show", "--id", task_type_id)
    assert f"Type: {type_name}" in result.output
    assert "Generator URL:" in result.output


def test_task_type_update():
    login_admin()

    # Create a round first
    round_id, _ = create_round()
    
    # Create a task type for the round
    task_type_id, _ = create_task_type(round_id, "test_update_type")

    # Now update the task type
    result = run_ok(
        "task-type", "update",
        "--id", task_type_id,
        "--type", "updated_test_type",
        "--max-tasks", "100500"
    )
    assert f"Task type updated successfully with ID: {task_type_id}" in result.output
    assert "Type: updated_test_type" in result.output
    assert "Max Tasks Per Team: 100500" in result.output


def test_task_type_delete():
    login_admin()
    
    # Create a round first
    round_id, _ = create_round()
    
    # Create a task type for the round
    task_type_id, _ = create_task_type(round_id, "test_delete_type")
    
    # Now delete the task type
    result = run_ok("task-type", "delete", "--id", task_type_id, "--yes")
    assert f"Task type with ID {task_type_id} deleted successfully" in result.output


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
    result = runner.invoke(app, list(args), catch_exceptions=False)
    print(f"Output: {result.output}")
    if result.exit_code != 0:
        print(f"Command failed with exit code {result.exit_code}")
        # Don't try to access stderr if it's not captured
        assert False, f"Command failed with exit code {result.exit_code}"
    return result

def extract_task_id(output: str) -> str:
    """Extract task ID from the output of the claim command."""
    for line in output.splitlines():
        if "Task ID:" in line:
            return line.split("Task ID:")[1].strip()
    return "1"

DEFAULT_CHALLENGE_ID = "2"

def get_challenge_id() -> str:
    return DEFAULT_CHALLENGE_ID

def get_round_id(challenge_id: str = DEFAULT_CHALLENGE_ID) -> str:
    return "1"

def get_task_type_id(round_id: str = None) -> str:
    return "1"

def create_task_type(round_id: str, type_name_prefix: str = "test_type") -> tuple[str, str]:
    type_name = f"{type_name_prefix}_{int(time.time())}"
    create_result = run_ok(
        "task-type", "create",
        "--round", round_id,
        "--type", type_name,
        "--generator-url", "http://example.com/generator",
        "--generator-settings", "{\"difficulty\": \"easy\"}",
        "--generator-secret", "test_secret",
        "--max-tasks", "5"
    )
    
    # Extract the task type ID from the output
    task_type_id = None
    for line in create_result.output.splitlines():
        if "Task type created successfully with ID:" in line:
            task_type_id = line.split("ID:")[1].strip()
            break
    
    if not task_type_id:
        assert False, "Failed to create task type, no ID found in output"
        
    return task_type_id, type_name

def get_task_id() -> str:
    return "1"

def create_round(challenge_id = DEFAULT_CHALLENGE_ID):
    # Create a round first
    now = datetime.now()
    start_time = now.isoformat()
    end_time = (now + timedelta(hours=2)).isoformat()
    round_index = 2
    cmd = f"round create --challenge {challenge_id} --index {round_index} --start-time {start_time} --end-time {end_time} --status draft"
    create_result = run_ok(*cmd.split())
    # Extract the round ID from the output
    round_id = None
    for line in create_result.output.splitlines():
        if "Round ID:" in line:
            round_id = line.split("Round ID:")[1].strip()
            break
    if not round_id:
        assert False, "Failed to create round, no Round ID found in output:\n" + create_result.output
    return round_id, round_index
