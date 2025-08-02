import typer
from pathlib import Path
from app_deps import api_client, json_output_option, console, ensure_logged_in
from formatter import print_as_json
from typing import Optional
from rich.table import Table

task_app = typer.Typer(help="Task management commands")

@task_app.command("claim")
def claim(
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Task type"),
    json: bool = json_output_option
):
    """Claim a new task."""
    ensure_logged_in()
    try:
        task = api_client.claim_task(task_type)

        if json:
            return print_as_json(task)

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
def task_show(task_id: str, json: bool = json_output_option):
    """Show task and its submissions."""
    ensure_logged_in()

    try:
        task = api_client.get_task_info(task_id)

        if json:
            return print_as_json(task)

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
def task_show_input(task_id: str, json: bool = json_output_option):
    """Show raw task input payload."""
    ensure_logged_in()

    try:
        task_input = api_client.get_task_input(task_id)

        if json:
            return print_as_json(task_input)

        console.print(task_input)

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("submit")
def task_submit(
    task_id: str,
    answer: Optional[str] = None,
    file_path: Optional[Path] = typer.Option(None, "--file", help="Path to file with answer"),
    json: bool = json_output_option
):
    """Submit an answer for a task."""
    ensure_logged_in()

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
        submission = api_client.submit_task_answer(task_id, answer)

        if json:
            return print_as_json(submission)

        console.print(f"[green]Successfully submitted answer for task {task_id}[/green]")
        console.print(f"Submission ID: {submission.id}")
        console.print(f"Status: {submission.status}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show-answer")
def task_show_answer(submit_id: str, json: bool = json_output_option):
    """Show raw submitted answer."""
    ensure_logged_in()

    try:
        submission = api_client.get_submission_info(submit_id)

        if json:
            return print_as_json(submission)

        raise Exception("Not implemented yet")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("list")
def task_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by task type"),
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Filter by round ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Show tasks since specified time"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = json_output_option
):
    """List tasks."""
    ensure_logged_in()

    try:
        tasks = api_client.list_tasks(status, task_type, round_id, since)

        if json:
            return print_as_json(tasks)

        table = Table(title="Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Type")
        table.add_column("Status", style="green")
        table.add_column("Score")
        table.add_column("Time Remaining")
        table.add_column("Claimed At")
        table.add_column("Last Attempt At")
        table.add_column("Solved At")

        for task in tasks.tasks:
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

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

