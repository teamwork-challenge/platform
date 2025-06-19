#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Create Typer app and command groups
app = typer.Typer(help="Teamwork Challenge CLI")
team_app = typer.Typer(help="Team management commands")
round_app = typer.Typer(help="Round management commands")
task_app = typer.Typer(help="Task management commands")
board_app = typer.Typer(help="Leaderboard and dashboard commands")

# Add command groups to main app
app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(board_app, name="board")

# Create console for rich output
console = Console()

# Config file path
CONFIG_PATH = Path.home() / ".challenge" / "config.json"


def get_api_key() -> Optional[str]:
    """Get API key from config file."""
    if not CONFIG_PATH.exists():
        return None
    
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            return config.get("api_key")
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    config["api_key"] = api_key
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


# Authentication commands
@app.command()
def login(api_key: str):
    """Store API key into config file after successful login."""
    # In a real implementation, we would validate the API key with the server
    save_api_key(api_key)
    console.print(f"[green]Successfully logged in with API key: {api_key}[/green]")


@app.command()
def logout():
    """Remove API key from config file."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            
            if "api_key" in config:
                del config["api_key"]
                
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f)
                
                console.print("[green]Successfully logged out[/green]")
            else:
                console.print("[yellow]Not logged in[/yellow]")
        except (json.JSONDecodeError, FileNotFoundError):
            console.print("[red]Error reading config file[/red]")
    else:
        console.print("[yellow]Not logged in[/yellow]")


@app.command()
def whoami():
    """Show team id and name."""
    api_key = get_api_key()
    if api_key:
        # In a real implementation, we would fetch team info from the server
        console.print(f"[green]Team ID: 123[/green]")
        console.print(f"[green]Team Name: Example Team[/green]")
    else:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")


# Team commands
@team_app.command("show")
def team_show():
    """Show team information."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch team info from the server
    console.print("[bold]Team Information:[/bold]")
    console.print(f"Team ID: 123")
    console.print(f"Team Name: Example Team")
    console.print(f"Members: 3")


@team_app.command("rename")
def team_rename(new_name: str):
    """Rename team (allowed until first submission)."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would update the team name on the server
    console.print(f"[green]Team renamed to: {new_name}[/green]")


# Challenge commands
@app.command("show")
def show():
    """Show challenge information."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch challenge info from the server
    console.print("[bold]Challenge Information:[/bold]")
    console.print("Name: Teamwork Challenge")
    console.print("Status: Active")
    console.print("Current Round: 1")
    console.print("Total Rounds: 3")


# Round commands
@round_app.command("show")
def round_show(round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID")):
    """Show round information."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # Use current round if not specified
    if round_id is None:
        round_id = 1  # In a real implementation, we would get this from the server
    
    # In a real implementation, we would fetch round info from the server
    console.print(f"[bold]Round {round_id} Information:[/bold]")
    console.print(f"Status: Active")
    console.print(f"Start Time: 2023-01-01 00:00:00")
    console.print(f"End Time: 2023-01-07 23:59:59")
    console.print(f"Tasks Available: 10")


@round_app.command("list")
def round_list():
    """List all rounds."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch rounds from the server
    table = Table(title="Rounds")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Start Time")
    table.add_column("End Time")
    
    table.add_row("1", "Active", "2023-01-01 00:00:00", "2023-01-07 23:59:59")
    table.add_row("2", "Upcoming", "2023-01-08 00:00:00", "2023-01-14 23:59:59")
    table.add_row("3", "Upcoming", "2023-01-15 00:00:00", "2023-01-21 23:59:59")
    
    console.print(table)


# Task commands
@task_app.command("claim")
def task_claim(task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Task type")):
    """Claim a new task."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would claim a task from the server
    task_id = "task123"
    task_type = task_type or "general"
    
    console.print(f"[green]Successfully claimed task:[/green]")
    console.print(f"Task ID: {task_id}")
    console.print(f"Task Type: {task_type}")
    console.print(f"Score: 100")
    console.print(f"Time Remaining: 24h")


@task_app.command("show")
def task_show(task_id: str):
    """Show task and its submissions."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch task info from the server
    console.print(f"[bold]Task {task_id} Information:[/bold]")
    console.print(f"Type: general")
    console.print(f"Status: PENDING")
    console.print(f"Score: 100")
    console.print(f"Time Remaining: 24h")
    console.print(f"Claimed At: 2023-01-01 12:00:00")
    
    console.print("\n[bold]Submissions:[/bold]")
    console.print("No submissions yet.")


@task_app.command("show-input")
def task_show_input(task_id: str):
    """Show raw task input payload."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch task input from the server
    task_input = {
        "id": task_id,
        "type": "general",
        "description": "This is a sample task",
        "data": {
            "input": [1, 2, 3, 4, 5]
        }
    }
    
    console.print(json.dumps(task_input, indent=2))


@task_app.command("submit")
def task_submit(
    task_id: str,
    answer: Optional[str] = None,
    file_path: Optional[Path] = typer.Option(None, "--file", help="Path to file with answer")
):
    """Submit an answer for a task."""
    api_key = get_api_key()
    if not api_key:
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
    
    # In a real implementation, we would submit the answer to the server
    submit_id = "submit456"
    
    console.print(f"[green]Successfully submitted answer for task {task_id}[/green]")
    console.print(f"Submission ID: {submit_id}")
    console.print(f"Status: PENDING")


@task_app.command("show-answer")
def task_show_answer(submit_id: str):
    """Show raw submitted answer."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch submission from the server
    submission = {
        "id": submit_id,
        "task_id": "task123",
        "status": "PENDING",
        "answer": "Sample answer",
        "submitted_at": "2023-01-01 14:30:00"
    }
    
    console.print(json.dumps(submission, indent=2))


@task_app.command("list")
def task_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by task type"),
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Filter by round ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Show tasks since specified time"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates")
):
    """List tasks."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # In a real implementation, we would fetch tasks from the server with filters
    table = Table(title="Tasks")
    table.add_column("Task ID", style="cyan")
    table.add_column("Type")
    table.add_column("Status", style="green")
    table.add_column("Score")
    table.add_column("Time Remaining")
    table.add_column("Claimed At")
    table.add_column("Last Attempt At")
    table.add_column("Solved At")
    
    table.add_row("task123", "general", "PENDING", "100", "24h", "2023-01-01 12:00:00", "", "")
    table.add_row("task456", "math", "AC", "75", "", "2023-01-01 10:00:00", "", "2023-01-01 11:30:00")
    table.add_row("task789", "coding", "WA", "50", "12h", "2023-01-01 09:00:00", "2023-01-01 10:15:00", "")
    
    console.print(table)
    
    if watch:
        console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
        # In a real implementation, we would poll for updates


# Board commands
@board_app.command("dashboard")
def board_dashboard(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates")
):
    """Show dashboard with task statistics."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # Use current round if not specified
    if round_id is None:
        round_id = 1  # In a real implementation, we would get this from the server
    
    # In a real implementation, we would fetch dashboard data from the server
    table = Table(title=f"Dashboard for Round {round_id}")
    table.add_column("Task Type", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("PENDING", justify="right")
    table.add_column("AC", justify="right")
    table.add_column("WA", justify="right")
    table.add_column("Remaining", justify="right")
    
    table.add_row("general", "10", "1", "5", "2", "2")
    table.add_row("math", "8", "0", "3", "1", "4")
    table.add_row("coding", "12", "2", "4", "3", "3")
    table.add_row("Total", "30", "3", "12", "6", "9")
    
    console.print(table)
    
    if watch:
        console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
        # In a real implementation, we would poll for updates


@board_app.command("leaderboard")
def board_leaderboard(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates")
):
    """Show leaderboard with team scores."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)
    
    # Use current round if not specified
    if round_id is None:
        round_id = 1  # In a real implementation, we would get this from the server
    
    # In a real implementation, we would fetch leaderboard data from the server
    table = Table(title=f"Leaderboard for Round {round_id}")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Team")
    table.add_column("General", justify="right")
    table.add_column("Math", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Total", justify="right", style="green")
    
    table.add_row("1", "Team Alpha", "500", "400", "600", "1500")
    table.add_row("2", "Team Beta", "450", "350", "550", "1350")
    table.add_row("3", "Team Gamma", "400", "300", "500", "1200")
    
    console.print(table)
    
    if watch:
        console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")
        # In a real implementation, we would poll for updates


if __name__ == "__main__":
    app()
