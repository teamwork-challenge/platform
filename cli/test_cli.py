#!/usr/bin/env python3
import sys
import logging
from typing import Iterator
from pathlib import Path

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
from back.tests.test_setup import clear_firestore_data, create_test_firebase_data

backend_port = 8918


@pytest.fixture(scope="session", autouse=True)
def start_server() -> Iterator[None]:
    project_root = Path(__file__).resolve().parents[1]  # .../platform
    print(f"Project root: {project_root}")
    os.chdir(project_root)  # make imports like 'back.*' work everywhere
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # nuke prior handlers so this actually applies
    )
    server_url = "http://127.0.0.1:" + str(backend_port)
    # Backup existing config to restore later (before we modify it)
    from cli.typers.app_deps import CONFIG_PATH  # imported late to use correct home
    backup_path = CONFIG_PATH.with_suffix(".test.bak")
    if CONFIG_PATH.exists():
        try:
            import shutil
            shutil.copy2(CONFIG_PATH, backup_path)
        except Exception:
            pass
    # Persist API URL in CLI config so ApiClient reads it via ConfigManager
    try:
        runner.invoke(app, ["config", "api-url", server_url], catch_exceptions=False)
    except Exception:
        # Fallback to env var to be extra safe
        os.environ["CHALLENGE_API_URL"] = server_url
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    clear_firestore_data()
    create_test_firebase_data()
    proc = subprocess.Popen(["uvicorn", "back.main:app", "--port", str(backend_port)])
    wait_endpoint_up(server_url, 1.0)

    try:
        yield
    finally:
        # Restore previous config
        try:
            import shutil
            if backup_path.exists():
                shutil.copy2(backup_path, CONFIG_PATH)
                backup_path.unlink(missing_ok=True)
            else:
                # No previous config; remove test config if created
                if CONFIG_PATH.exists():
                    CONFIG_PATH.unlink()
        except Exception:
            pass
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
    assert "500" not in str(result.exception)


def test_logout() -> None:
    login_team1()
    result = run_ok("logout")
    assert "Successfully logged out" in result.output


def test_challenge_show_ok() -> None:
    login_team1()
    result = run_ok("challenge", "show", "-c", "challenge_1")
    assert "Challenge" in result.output


def test_challenge_update() -> None:
    login_admin()
    result = run_ok("challenge", "update", "cli/test_data/challenge1.hjson")
    assert "Temporary Challenge" in result.output


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
    result = run_ok("round", "update", "cli/test_data/round_temp.hjson")
    assert "r_temp" in result.output


def test_round_update() -> None:
    login_admin()
    run_ok("round", "update", "cli/test_data/round_temp.hjson")
    result = run_ok("round", "update", "cli/test_data/round_temp.hjson")
    assert "r_temp" in result.output


def test_round_delete() -> None:
    login_admin()

    run_ok("round", "update", "cli/test_data/round_temp.hjson")
    result = run_ok("round", "list", "-c", "challenge_1")
    assert f"r_temp" in result.output

    run_ok("round", "delete", "-r", "r_temp", "-c", "challenge_1", "--yes")
    result = run_ok("round", "list", "-c", "challenge_1")
    assert f"r_temp" not in result.output


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

# New tests for rename team and get challenges

def test_team_rename() -> None:
    login_team1()

    new_name = "New {Team:} Name"
    result = run_ok("team", "rename", new_name)

    result = run_ok("team", "show")
    assert new_name in result.output


def test_get_challenges_admin() -> None:
    login_admin()
    result = run_ok("challenge", "list")
    assert "challenge_1" in result.output
    assert "challenge_2" in result.output


def test_team_create_batch() -> None:
    # Admin should be able to create teams in bulk via TSV file
    login_admin()
    # Prepare TSV content with optional header
    tsv_lines = [
        "name\tmembers\tcaptain_contact",
        "Alpha Team\tAlice,Bob\talpha@example.com",
        "Beta Team\tCarol,Dan\tbeta@example.com",
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
        f.write("\n".join(tsv_lines))
        temp_file = f.name

    try:
        result = run_ok("team", "create", "challenge_2", temp_file)
        # Should return JSON payload containing created teams
        assert "Alpha Team" in result.output
        assert "Beta Team" in result.output
        assert "challenge_2" in result.output
    finally:
        os.unlink(temp_file)


def test_team_list() -> None:
    # Admin can list teams for a specific challenge using top-level `teams` command
    login_admin()
    result = run_ok("team", "list", "challenge_1")
    # Expect to see at least team_1 from seed data
    assert "team_1" in result.output


def test_config_api_url_and_persist() -> None:
    # Set API URL via CLI and ensure it's persisted
    server_url = f"http://127.0.0.1:{backend_port}"
    result = run_ok("config", "api-url", server_url)
    assert f"API URL set to {server_url}" in result.output
    # Verify ConfigManager reads it back
    from cli.typers.app_deps import config_manager
    assert config_manager.get_base_url() == server_url


def test_config_log_level_validation_and_persist() -> None:
    # Invalid destination
    res = runner.invoke(app, ["config", "log-level", "screen", "INFO"], catch_exceptions=False)
    assert res.exit_code == 2
    assert "Invalid destination" in res.output
    # Invalid level
    res = runner.invoke(app, ["config", "log-level", "console", "NONE"], catch_exceptions=False)
    assert res.exit_code == 2
    assert "Invalid level" in res.output
    # Valid settings persist
    ok = run_ok("config", "log-level", "console", "WARNING")
    assert "Set console log level to WARNING" in ok.output
    ok = run_ok("config", "log-level", "file", "ERROR")
    assert "Set file log level to ERROR" in ok.output
    from cli.typers.app_deps import config_manager as _cfg
    levels = _cfg.get("log_levels") or {}
    # Defaults preserved for unspecified, values updated for specified
    assert levels.get("console") == "WARNING"
    assert levels.get("file") == "ERROR"


def test_team_list_admin_includes_api_key() -> None:
    # team list is under team app and requires admin; output should include API Key
    login_admin()
    res = run_ok("team", "list", "challenge_1")
    assert "API Key" in res.output
    assert "team1" in res.output


def test_help_on_invalid_command_shows_help() -> None:
    # Invalid/malformed command should show help immediately
    res = runner.invoke(app, ["teem"], catch_exceptions=False)
    assert res.exit_code != 0
    # Typer shows usage/help content
    assert "Usage" in res.output or "Commands" in res.output


def test_logging_console_level_controls_output() -> None:
    # Ensure logged-in and server URL are set
    login_team1()
    # First set to CRITICAL and verify logs are suppressed
    run_ok("config", "log-level", "console", "CRITICAL")
    out = subprocess.run([sys.executable, "-m", "cli.main", "team", "show"], capture_output=True, text=True)
    assert out.returncode == 0
    assert "Make request:" not in out.stdout
    # Now set to DEBUG and verify logs are shown
    run_ok("config", "log-level", "console", "DEBUG")
    out2 = subprocess.run([sys.executable, "-m", "cli.main", "team", "show"], capture_output=True, text=True)
    assert out2.returncode == 0
    assert "Make request:" in out2.stdout
