#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Union
import dataclasses

import typer
from rich.console import Console
from rich.table import Table

from api_client import ApiClient
from models import Team, Challenge, Round, Task, Submission, TaskList, Dashboard, Leaderboard, RoundList

# Create Typer app and command groups with global --json option
class AppWithJson(typer.Typer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_option = None

    def callback(self, *args, **kwargs):
        # Add --json option to the callback
        json_option = typer.Option(False, "--json", help="Output in JSON format")
        if "json" not in kwargs.get("params", {}):
            kwargs.setdefault("params", {})["json"] = json_option
        return super().callback(*args, **kwargs)

app = AppWithJson(help="Teamwork Challenge CLI")
team_app = AppWithJson(help="Team management commands")
round_app = AppWithJson(help="Round management commands")
task_app = AppWithJson(help="Task management commands")
board_app = AppWithJson(help="Leaderboard and dashboard commands")

# Add command groups to main app
app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(board_app, name="board")

# Create console for rich output
console = Console()

# Config file path
CONFIG_PATH = Path.home() / ".challenge" / "config.json"

# Create API client with API key from config file
api_client = ApiClient()

# Decorator for handling JSON output
def handle_json_output(f: Callable) -> Callable:
    """Decorator to handle JSON output based on --json flag."""
    def wrapper(*args, **kwargs):
        # Extract json flag from kwargs
        json_output = kwargs.pop("json", False)

        # Call the original function which should return model class instance
        result = f(*args, **kwargs)

        # If --json flag is set, convert the model to a dictionary and print as JSON
        if json_output and result is not None:
            if hasattr(result, '__dict__'):
                # If it's a simple object with __dict__
                result_dict = result.__dict__
            elif dataclasses.is_dataclass(result):
                # If it's a dataclass
                result_dict = dataclasses.asdict(result)
            else:
                # If it's already a dict or something else
                result_dict = result

            console.print(json.dumps(result_dict, indent=2))
            return None
        else:
            # Otherwise, let the function handle the formatting
            return result

    return wrapper


# These functions are now handled by the ApiClient class


# Authentication commands
@app.command()
@handle_json_output
def login(api_key: str, json: bool = False):
    """Store API key into config file after successful login."""
    try:
        # Create a new ApiClient with the provided API key
        global api_client
        api_client = ApiClient(api_key=api_key)

        # Validate the API key with the server
        if not api_client.validate_api_key(api_key):
            if json:
                return {"status": "error", "message": "Invalid API key"}

            console.print("[red]Invalid API key[/red]")
            raise typer.Exit(1)

        # Save the API key
        api_client.save_api_key(api_key)

        # If json flag is set, return a success message as JSON
        if json:
            return {"status": "success", "message": f"Successfully logged in with API key: {api_key}"}

        console.print(f"[green]Successfully logged in with API key: {api_key}[/green]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
@handle_json_output
def logout(json: bool = False):
    """Remove API key from config file."""
    try:
        success = api_client.remove_api_key()

        # Create a new ApiClient without an API key
        global api_client
        api_client = ApiClient()

        # If json flag is set, return the result as JSON
        if json:
            if success:
                return {"status": "success", "message": "Successfully logged out"}
            else:
                return {"status": "warning", "message": "Not logged in"}

        if success:
            console.print("[green]Successfully logged out[/green]")
        else:
            console.print("[yellow]Not logged in[/yellow]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
@handle_json_output
def whoami(json: bool = False):
    """Show team id and name."""
    if not api_client.api_key:
        if json:
            return {"status": "error", "message": "Not logged in"}

        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        return None

    try:
        # Get team info from the API
        team = api_client.get_team_info()

        # If json flag is set, the decorator will handle the output
        if json:
            return team

        # Otherwise, format the data for human-readable output
        console.print(f"[green]Team ID: {team.id}[/green]")
        console.print(f"[green]Team Name: {team.name}[/green]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


# Team commands
@team_app.command("show")
@handle_json_output
def team_show(json: bool = False):
    """Show team information."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get team info from the API
        team = api_client.get_team_info()

        # If json flag is set, the decorator will handle the output
        if json:
            return team

        # Otherwise, format the data for human-readable output
        console.print("[bold]Team Information:[/bold]")
        console.print(f"Team ID: {team.id}")
        console.print(f"Team Name: {team.name}")
        console.print(f"Members: {team.member_count}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@team_app.command("rename")
@handle_json_output
def team_rename(new_name: str, json: bool = False):
    """Rename team (allowed until first submission)."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Rename team using the API
        team = api_client.rename_team(new_name)

        # If json flag is set, the decorator will handle the output
        if json:
            return team

        # Otherwise, format the data for human-readable output
        console.print(f"[green]Team renamed to: {team.name}[/green]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


# Challenge commands
@app.command("show")
@handle_json_output
def show(json: bool = False):
    """Show challenge information."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get challenge info from the API
        challenge = api_client.get_challenge_info()

        # If json flag is set, the decorator will handle the output
        if json:
            return challenge

        # Otherwise, format the data for human-readable output
        console.print("[bold]Challenge Information:[/bold]")
        console.print(f"Name: {challenge.name}")
        console.print(f"Status: {challenge.status}")
        console.print(f"Current Round: {challenge.current_round}")
        console.print(f"Total Rounds: {challenge.total_rounds}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


# Round commands
@round_app.command("show")
@handle_json_output
def round_show(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    json: bool = False
):
    """Show round information."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get round info from the API
        round_info = api_client.get_round_info(round_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return round_info

        # Otherwise, format the data for human-readable output
        console.print(f"[bold]Round {round_info.id} Information:[/bold]")
        console.print(f"Status: {round_info.status}")
        console.print(f"Start Time: {round_info.start_time}")
        console.print(f"End Time: {round_info.end_time}")
        console.print(f"Tasks Available: {round_info.tasks_available}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("list")
@handle_json_output
def round_list(json: bool = False):
    """List all rounds."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get rounds from the API
        round_list = api_client.list_rounds()

        # If json flag is set, the decorator will handle the output
        if json:
            return round_list

        # Otherwise, format the data for human-readable output
        table = Table(title="Rounds")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Start Time")
        table.add_column("End Time")

        for round_info in round_list.rounds:
            table.add_row(
                str(round_info.id),
                round_info.status,
                round_info.start_time,
                round_info.end_time
            )

        console.print(table)
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


# Task commands
@task_app.command("claim")
@handle_json_output
def task_claim(
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Task type"),
    json: bool = False
):
    """Claim a new task."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Claim a task from the API
        task = api_client.claim_task(task_type)

        # If json flag is set, the decorator will handle the output
        if json:
            return task

        # Otherwise, format the data for human-readable output
        console.print(f"[green]Successfully claimed task:[/green]")
        console.print(f"Task ID: {task.id}")
        console.print(f"Task Type: {task.type}")
        console.print(f"Score: {task.score}")
        console.print(f"Time Remaining: {task.time_remaining}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show")
@handle_json_output
def task_show(task_id: str, json: bool = False):
    """Show task and its submissions."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get task info from the API
        task = api_client.get_task_info(task_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return task

        # Otherwise, format the data for human-readable output
        console.print(f"[bold]Task {task_id} Information:[/bold]")
        console.print(f"Type: {task.type}")
        console.print(f"Status: {task.status}")
        console.print(f"Score: {task.score}")
        console.print(f"Time Remaining: {task.time_remaining}")
        console.print(f"Claimed At: {task.claimed_at}")

        console.print("\n[bold]Submissions:[/bold]")
        if not task.submissions:
            console.print("No submissions yet.")
        else:
            for submission in task.submissions:
                console.print(f"ID: {submission.id}")
                console.print(f"Status: {submission.status}")
                console.print(f"Submitted At: {submission.submitted_at}")
                console.print("")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show-input")
@handle_json_output
def task_show_input(task_id: str, json: bool = False):
    """Show raw task input payload."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get task input from the API
        task_input = api_client.get_task_input(task_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return task_input

        # Otherwise, format the data for human-readable output
        console.print(json.dumps(task_input, indent=2))

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("submit")
@handle_json_output
def task_submit(
    task_id: str,
    answer: Optional[str] = None,
    file_path: Optional[Path] = typer.Option(None, "--file", help="Path to file with answer"),
    json: bool = False
):
    """Submit an answer for a task."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    if answer is None and file_path is None:
        console.print("[red]Either answer or --file must be provided[/red]")
        raise typer.Exit(1)

    if file_path:
        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        with open(file_path) as f:
            answer = f.read()

    try:
        # Submit the answer to the API
        submission = api_client.submit_task_answer(task_id, answer)

        # If json flag is set, the decorator will handle the output
        if json:
            return submission

        # Otherwise, format the data for human-readable output
        console.print(f"[green]Successfully submitted answer for task {task_id}[/green]")
        console.print(f"Submission ID: {submission.id}")
        console.print(f"Status: {submission.status}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show-answer")
@handle_json_output
def task_show_answer(submit_id: str, json: bool = False):
    """Show raw submitted answer."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get submission from the API
        submission = api_client.get_submission_info(submit_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return submission

        # Otherwise, format the data for human-readable output
        # Convert the submission to a dictionary for display
        submission_dict = dataclasses.asdict(submission)
        console.print(json.dumps(submission_dict, indent=2))

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("list")
@handle_json_output
def task_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by task type"),
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Filter by round ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Show tasks since specified time"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = False
):
    """List tasks."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get tasks from the API with filters
        task_list = api_client.list_tasks(status, task_type, round_id, since)

        # If json flag is set, the decorator will handle the output
        if json:
            return task_list

        # Otherwise, format the data for human-readable output
        table = Table(title="Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Type")
        table.add_column("Status", style="green")
        table.add_column("Score")
        table.add_column("Time Remaining")
        table.add_column("Claimed At")
        table.add_column("Last Attempt At")
        table.add_column("Solved At")

        for task in task_list.tasks:
            table.add_row(
                task.id,
                task.type,
                task.status,
                str(task.score),
                task.time_remaining,
                task.claimed_at,
                task.last_attempt_at or "N/A",
                task.solved_at or "N/A"
            )

        console.print(table)

        if watch:
            console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
            # In a real implementation, we would poll for updates

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


# Board commands
@board_app.command("dashboard")
@handle_json_output
def board_dashboard(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = False
):
    """Show dashboard with task statistics."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get dashboard data from the API
        dashboard = api_client.get_dashboard(round_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return dashboard

        # Otherwise, format the data for human-readable output
        table = Table(title=f"Dashboard for Round {dashboard.round_id}")
        table.add_column("Task Type", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("PENDING", justify="right")
        table.add_column("AC", justify="right")
        table.add_column("WA", justify="right")
        table.add_column("Remaining", justify="right")

        for task_type, type_stats in dashboard.stats.items():
            if task_type != 'total':  # Handle total separately
                table.add_row(
                    task_type,
                    str(type_stats.total),
                    str(type_stats.pending),
                    str(type_stats.ac),
                    str(type_stats.wa),
                    str(type_stats.remaining)
                )

        # Add total row if available
        if 'total' in dashboard.stats:
            total_stats = dashboard.stats['total']
            table.add_row(
                "Total",
                str(total_stats.total),
                str(total_stats.pending),
                str(total_stats.ac),
                str(total_stats.wa),
                str(total_stats.remaining)
            )

        console.print(table)

        if watch:
            console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
            # In a real implementation, we would poll for updates

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@board_app.command("leaderboard")
@handle_json_output
def board_leaderboard(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = False
):
    """Show leaderboard with team scores."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get leaderboard data from the API
        leaderboard = api_client.get_leaderboard(round_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return leaderboard

        # Otherwise, format the data for human-readable output
        table = Table(title=f"Leaderboard for Round {leaderboard.round_id}")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Team")
        table.add_column("General", justify="right")
        table.add_column("Math", justify="right")
        table.add_column("Coding", justify="right")
        table.add_column("Total", justify="right", style="green")

        for team in leaderboard.teams:
            table.add_row(
                str(team.rank),
                team.name,
                str(team.scores.get('general', 'N/A')),
                str(team.scores.get('math', 'N/A')),
                str(team.scores.get('coding', 'N/A')),
                str(team.total_score)
            )

        console.print(table)

        if watch:
            console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
            # In a real implementation, we would poll for updates

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
