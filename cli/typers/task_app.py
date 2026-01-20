import typer
import json
from pathlib import Path

from api_models import SubmitAnswerRequest
from cli.typers.app_deps import api_client, json_output_option, console, ensure_logged_in
from cli.formatter import print_as_json
from typing import Optional
from rich.table import Table

task_app = typer.Typer(help="Task management commands")


@task_app.command("claim")
def claim(
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Task type"),
    json: bool = json_output_option
) -> None:
    """Claim a new task."""
    ensure_logged_in()
    task = api_client.claim_task(task_type)

    if json:
        return print_as_json(task)

    console.print(f"[green]Successfully claimed task:[/green]")
    console.print(f"Task ID: {task.id}")
    console.print(f"Task Type: {task.type}")
    console.print(f"Score: {task.score}")

    return None


@task_app.command("show")
def task_show(task_id: str, json: bool = json_output_option) -> None:
    """Show a task and its submissions.

    If the task statement is short (< 200 characters), also show its statement and input here.
    For longer statements, keep an output compact and suggest using `task show-input`.
    """
    ensure_logged_in()

    task = api_client.get_task_info(task_id)

    if json:
        return print_as_json(task)

    console.print(f"[bold]Task {task_id} Information:[/bold]")
    console.print(f"Type: {task.type}")
    console.print(f"Status: {task.status}")
    console.print(f"Score: {task.score}")
    console.print(f"Claimed At: {task.claimed_at}")

    # Show statement and input inline only when the statement is short
    statement = getattr(task, "statement", None)
    input_payload = getattr(task, "input", None)
    if statement is not None:
        if len(str(statement)) < 200:
            console.print("\n[bold]Statement:[/bold]")
            console.print(str(statement))
            if input_payload is not None:
                console.print("\n[bold]Input:[/bold]")
                console.print(str(input_payload))
        else:
            console.print("\n[bold]Statement:[/bold] (too long to display inline)")
            console.print(f"Use `task show-input {task_id}` to see the full input.")
    elif input_payload is not None:
        # If there is no statement but there is input, and it's short, show it
        if len(str(input_payload)) < 200:
            console.print("\n[bold]Input:[/bold]")
            console.print(str(input_payload))
        else:
            console.print("\n[bold]Input:[/bold] (too long to display inline)")
            console.print(f"Use `task show-input {task_id}` to see the full input.")

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


@task_app.command("show-input")
def task_show_input(task_id: str, json: bool = json_output_option) -> None:
    """Show raw task input payload."""
    ensure_logged_in()

    task_input = api_client.get_task_input(task_id)

    if json:
        return print_as_json(task_input)

    console.print(task_input)

    return None


@task_app.command("submit")
def task_submit(
    task_id: str,
    answer: Optional[str] = typer.Argument(None, help="Answer to submit"),
    file_path: Optional[Path] = typer.Option(None, "--file", help="Path to file with answer"),
    json: bool = json_output_option
) -> None:
    """Submit an answer for the task."""
    ensure_logged_in()

    if answer is None and file_path is None:
        console.print("[red]Either answer or --file must be provided[/red]")
        raise typer.Exit(1)

    if file_path:
        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        with open(file_path, encoding='utf-8') as f:
            answer = f.read()

    if answer is None:
        raise ValueError("Answer cannot be None")

    submission = api_client.submit_task_answer(SubmitAnswerRequest(task_id=task_id, answer=answer))

    if json:
        return print_as_json(submission)

    # Keep backward-compatible output format expected by tests
    status_str = f"SubmissionStatus.{submission.status.name}"

    # Historical tests expect numeric ID without the 'task_' prefix in the message
    id_for_msg = task_id.replace('task_', '')
    console.print(f"[green]Successfully submitted answer for task {id_for_msg}[/green]")
    console.print(f"Submission ID: {submission.id}")
    console.print(f"Status: {status_str}")
    if submission.checker_output != "":
        console.print(f"Message: {submission.checker_output}")
    return None


@task_app.command("show-answer")
def task_show_answer(submit_id: str, json: bool = json_output_option) -> None:
    """Show raw submitted answer."""
    ensure_logged_in()

    submission = api_client.get_submission_info(submit_id)

    if json:
        return print_as_json(submission)

    console.print(f"[bold]Submission {submit_id} Information:[/bold]")
    console.print(f"Task ID: {submission.task_id}")
    console.print(f"Status: {submission.status}")
    console.print(f"Score: {submission.score}")
    console.print(f"Submitted At: {submission.submitted_at}")
    if submission.checker_output:
        console.print(f"Checker Output: {submission.checker_output}")
    console.print("\n[bold]Answer:[/bold]")
    console.print(submission.answer)

    return None


@task_app.command("list")
def task_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by task type"),
    round_id: Optional[str] = typer.Option(None, "--round", "-r", help="Filter by round ID"),
    since: Optional[str] = typer.Option(None, "--since", help="Show tasks since specified time"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = json_output_option
) -> None:
    """List tasks."""
    ensure_logged_in()

    # Fetch tasks with optional filters
    tasks = api_client.list_tasks(
        status=status,
        task_type=task_type,
        round_id=round_id,
        since=since
    )

    if json:
        return print_as_json(tasks)

    table = Table(title=f"Tasks (shown {len(tasks.tasks)} last tasks):")
    table.add_column("Task ID", style="cyan")
    table.add_column("Type")
    table.add_column("Status", style="green")
    table.add_column("Score")
    table.add_column("Claimed At")
    if status != "pending":
        table.add_column("Last Attempt At")
    if status == "ac":
        table.add_column("Solved At")

    for task in tasks.tasks:
        cells = [
            str(task.id),
            task.type,
            task.status,
            str(task.score),
            str(task.claimed_at)
        ]
        if status != "pending":
            cells.append(str(task.last_attempt_at) or "N/A")
        if status == "ac":
            cells.append(str(task.solved_at) or "N/A")
        table.add_row(*cells)

    console.print(table)

    if watch:
        console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")

    return None


def _format_checker_hint(hint: str, task_type: str) -> str:
    """Format checker hint, pretty-printing JSON if it's valid JSON.
    For tricky_maze tasks, only display the neighborhood field with decoded escape sequences.
    """
    try:
        # Try to parse as JSON
        parsed = json.loads(hint)
        
        # Special handling for tricky_maze: only show neighborhood field
        if task_type == "tricky_maze" and isinstance(parsed, dict) and "neighborhood" in parsed:
            neighborhood = parsed["neighborhood"]
            # Decode escape sequences (e.g., \n -> actual newline)
            if isinstance(neighborhood, str):
                return neighborhood.encode('latin-1').decode('unicode_escape')
            return str(neighborhood)
        
        # For other types, pretty-print the full JSON
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        # If it's not JSON, return as-is
        return hint


@task_app.command("report")
def task_report(
    task_type: str = typer.Option(..., "--type", "-t", help="Task type to generate report for"),
    challenge_id: str = typer.Option(..., "--challenge", "-c", help="Challenge ID"),
    round_id: str = typer.Option(..., "--round", "-r", help="Round ID"),
) -> None:
    """Generate a report of all tasks of a specific type.
    Generates all tasks by calling task generator and saves to reports/report_{task_type}.txt
    Admin only. Requires explicit challenge_id and round_id.
    """
    ensure_logged_in()
    
    # Get all generated tasks
    tasks = api_client.get_tasks_report(task_type, challenge_id, round_id)
    
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Write report file
    report_file = reports_dir / f"report_{task_type}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        for i, task in enumerate(tasks, 1):
            f.write(f"=== Task {i} ===\n")
            f.write(f"Statement:\n{task.statement}\n\n")
            f.write(f"Input:\n{task.input}\n\n")
            f.write(f"Checker Hint:\n{_format_checker_hint(task.checker_hint, task_type)}\n\n")
            f.write("-" * 80 + "\n\n")
    
    console.print(f"[green]Report generated: {report_file}[/green]")
    console.print(f"Generated {len(tasks)} tasks of type '{task_type}'")

    return None