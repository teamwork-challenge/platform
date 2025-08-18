#!/usr/bin/env python3
import sys
import logging
from typing import Iterator

from requests import HTTPError
from typer.testing import CliRunner
from click.testing import Result
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
from back.firebase_test_setup import clear_firestore_data, create_test_firebase_data

backend_port = 8918


@pytest.fixture(scope="session", autouse=True)
def start_server() -> Iterator[None]:
    if os.getcwd().endswith("cli"):
        os.chdir("..")
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # nuke prior handlers so this actually applies
    )
    server_url = "http://127.0.0.1:" + str(backend_port)
    os.environ["CHALLENGE_API_URL"] = server_url  # make CLI use the same port
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    clear_firestore_data()
    create_test_firebase_data()
    proc = subprocess.Popen(["uvicorn", "back.main:app", "--port", str(backend_port)], cwd="..", )
    wait_endpoint_up(server_url, 1.0)

    yield
    proc.terminate()
    proc.wait()


def wait_endpoint_up(server_url: str, max_wait_time: float) -> None:
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(server_url, timeout=1)
            if response.status_code == 200:
                break
        except RequestException:
            time.sleep(0.1)


runner = CliRunner()


# Challenge App Tests
def test_login_ok() -> None:
    result = login_team1()
    assert "Successfully logged in" in result.output


def test_login_fail() -> None:
    result = runner.invoke(app, ["login", "team1123123"], catch_exceptions=True)
    print(f"Stdout:\n{result.output}")
    print(f"Stderr:\n{result.stderr}")
    print(f"Exception:\n{result.exception}")
    assert result.exit_code != 0
    assert "Invalid API key" in str(result.exception)


def test_logout() -> None:
    login_team1()
    result = run_ok("logout")
    assert "Successfully logged out" in result.output


def test_challenge_show_ok() -> None:
    login_team1()
    result = run_ok("show", "-c", "challenge_1")
    assert "Challenge" in result.output


def test_challenge_update() -> None:
    login_admin()
    result = run_ok("update", "cli/test_data/challenge1.hjson")
    assert "Super Challenge 1" in result.output


# Team App Tests
def test_team_show_ok() -> None:
    login_team1()
    result = run_ok("team", "show")
    assert "Team ID: team_1" in result.output


# Round App Tests
def test_round_show() -> None:
    login_team1()

    result = run_ok("round", "show", "-r", "round_1")
    round_id = extract_from_output(result.output, "RoundID:")
    assert round_id == "round_1"


def test_round_list() -> None:
    login_team1()
    result = run_ok("round", "list")
    assert "Rounds" in result.output
    assert "Round round_1" in result.output


def test_round_create() -> None:
    login_admin()
    result = run_ok("round", "update", "cli/test_data/round1.hjson")
    assert "r1" in result.output


def test_round_update() -> None:
    login_admin()
    run_ok("round", "update", "cli/test_data/round1.hjson")
    result = run_ok("round", "update", "cli/test_data/round1.hjson")
    assert "r1" in result.output


def test_round_delete() -> None:
    login_admin()

    run_ok("round", "update", "cli/test_data/round1.hjson")
    result = run_ok("round", "list", "-c", "challenge_1")
    assert f"r1" in result.output

    run_ok("round", "delete", "-r", "r1", "-c", "challenge_1", "--yes")
    result = run_ok("round", "list", "-c", "challenge_1")
    assert f"r1" not in result.output


# Task App Tests
def test_task_claim() -> None:
    login_team1()
    result = run_ok("task", "claim", "--type", "a_plus_b")
    assert "Task ID:" in result.output


def test_task_show() -> None:
    login_team1()
    task_id = get_task_id()

    result = run_ok("task", "show", task_id)
    # Expect a short statement and input to be shown inline
    assert "Statement:" in result.output
    assert "Given two integers a and b" in result.output
    assert "Input:" in result.output
    assert "1 2" in result.output


def test_task_show_input() -> None:
    login_team1()
    task_id = get_task_id()

    result = run_ok("task", "show-input", task_id)
    assert "1 2" in result.output


def test_task_submit_file() -> None:
    login_team1()
    task_id = get_task_id()

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("some wrong answer")
        temp_file = f.name

    try:
        result = run_ok("task", "submit", task_id, "--file", temp_file)
        assert "Successfully submitted answer for task 1" in result.output
        assert "Status: SubmissionStatus.WA" in result.output
    finally:
        os.unlink(temp_file)


def test_task_submit_correct_answer() -> None:
    login_team1()
    task_id = get_task_id()
    # For the built-in a_plus_b task, input is "1 2", the correct answer is "3"
    result = run_ok("task", "submit", task_id, "3")
    assert "Successfully submitted answer for task 1" in result.output
    assert "Status: SubmissionStatus.AC" in result.output


def test_task_submit_without_file_or_answer() -> None:
    login_team1()
    task_id = get_task_id()
    # Invoke directly to check non-zero exit on missing both answer and --file
    result = runner.invoke(app, ["task", "submit", task_id], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Either answer or --file must be provided" in result.output


def test_task_list() -> None:
    login_team1()
    run_ok("task", "list")


def test_task_list_with_filter() -> None:
    login_team1()
    result = run_ok("task", "list", "--status", "pending")
    assert "a_plus_b" in result.output
    result = run_ok("task", "list", "--status", "ac")
    assert "tst_ac" not in result.output


def test_task_list_with_paging() -> None:
    login_team1()
    for i in range(21):
        run_ok("task", "claim", "--type", "a_plus_b")
    result = run_ok("task", "list", "--status", "pending")
    assert "20 last tasks" in result.output
    assert "Solved" not in result.output
    assert "Attempt" not in result.output



# Board App Tests
@pytest.mark.skip(reason="Board app is not yet implemented")
def test_board_dashboard() -> None:
    login_team1()
    result = run_ok("board", "dashboard")
    assert "Dashboard for Round" in result.output


@pytest.mark.skip(reason="Board app is not yet implemented")
def test_board_leaderboard() -> None:
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
    try:
        result = runner.invoke(app, list(args), catch_exceptions=False)
        print(f"Stdout:\n{result.output}")
        if result.exit_code != 0:
            print(f"Stderr:\n{result.stderr}")
            print(f"Exception:\n{result.exception}")
            # Don't try to access stderr if it's not captured
            assert False, f"Command failed with exit code {result.exit_code}"
        return result
    except HTTPError as e:
        print(f"Error: {e}")
        assert False, f"Command failed with exception"


def extract_task_id(output: str) -> str:
    """Extract task ID from the output of the claim command."""
    for line in output.splitlines():
        if "Task ID:" in line:
            return line.split("Task ID:")[1].strip()
    return "1"


DEFAULT_CHALLENGE_ID = "challenge_2"



def create_task_type(round_id: str, type_name_prefix: str = "test_type") -> str:
    type_name = f"{type_name_prefix}_{int(time.time())}"
    create_result = run_ok(
        "task-type", "create",
        "--round", round_id,
        "--type", type_name,
        "--generator-url", "https://example.com/generator",
        "--generator-settings", "{\"difficulty\": \"easy\"}",
        "--generator-secret", "test_secret",
        "--n-tasks", "5"
    )
    
    task_type = extract_from_output(create_result.output, "Task type created successfully:")
    return task_type


def get_task_id() -> str:
    return "task_1"


def create_round(challenge_id:str = DEFAULT_CHALLENGE_ID) -> str:
    # Create a round first
    now = datetime.now()
    start_time = now.isoformat()
    end_time = (now + timedelta(hours=2)).isoformat()
    cmd = (
        f"round create --challenge {challenge_id} "
        f"--start-time {start_time} --end-time {end_time} --status draft"
    )
    create_result = run_ok(*cmd.split())
    # Extract the round ID from the output
    round_id = extract_from_output(create_result.output, "Round ID:")
    if not round_id:
        assert False, "Failed to create round, no Round ID found in output:\n" + create_result.output
    return round_id

def extract_from_output(output: str, key: str) -> str:
    for line in output.splitlines():
        if key in line:
            return line.split(key)[1].strip()
    return ""