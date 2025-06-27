#!/usr/bin/env python3
from typer.testing import CliRunner, Result
from main import app

runner = CliRunner()

def test_login_ok():
    login_team1()

def test_login_fail():
    result = runner.invoke(app, ["login", "team1123123"])
    assert result.exit_code != 0

def test_team_show_ok():
    login_team1()
    result = run_ok("team", "show")
    assert "Team 1" in result.output

def test_list_show_ok():
    login_team1()
    result = run_ok("task", "list")
    assert "Task" in result.output


def login_team1() -> Result:
    return run_ok("login", "team1")

def run_ok(*args: str) -> Result:
    result = runner.invoke(app, list(args))
    if result.exit_code != 0:
        print(f"Command failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        assert False, f"Command failed with exit code {result.exit_code}"
    return result
