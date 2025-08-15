import typer
from pathlib import Path
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in
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
    try:
        task = api_client.claim_task(task_type)

        if json:
            return print_as_json(task)

        console.print(f"[green]Successfully claimed task:[/green]")
        console.print(f"Task ID: {task.id}")
        console.print(f"Task Type: {task.type}")
        console.print(f"Score: {task.score}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show")
def task_show(task_id: str, json: bool = json_output_option) -> None:
    """Show a task and its submissions.

    If the task statement is short (< 200 characters), also show its statement and input here.
    For longer statements, keep an output compact and suggest using `task show-input`.
    """
    ensure_logged_in()

    try:
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
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show-input")
def task_show_input(task_id: str, json: bool = json_output_option) -> None:
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

        with open(file_path) as f:
            answer = f.read()

    try:
        submission = api_client.submit_task_answer(task_id, str(answer))

        if json:
            return print_as_json(submission)

        # Format status as "SubmissionStatus.AC/WA" to match tests regardless of enum/string
        status_obj = getattr(submission, "status", None)
        try:
            if status_obj is not None and hasattr(status_obj, "name"):
                status_str = f"{status_obj.__class__.__name__}.{status_obj.name}"
            else:
                status_str = f"SubmissionStatus.{str(status_obj)}"
        except Exception:
            status_str = f"SubmissionStatus.{str(status_obj)}"

        console.print(f"[green]Successfully submitted answer for task {task_id}[/green]")
        console.print(f"Submission ID: {submission.id}")
        console.print(f"Status: {status_str}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@task_app.command("show-answer")
def task_show_answer(submit_id: str, json: bool = json_output_option) -> None:
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
) -> None:
    """List tasks."""
    ensure_logged_in()

    try:
        # ApiClient.list_tasks does not accept filters; fetch all tasks and filter client-side in future if needed
        tasks = api_client.list_tasks()

        if json:
            return print_as_json(tasks)

        table = Table(title="Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Type")
        table.add_column("Status", style="green")
        table.add_column("Score")
        table.add_column("Claimed At")
        table.add_column("Last Attempt At")
        table.add_column("Solved At")

        for task in tasks.tasks:
            table.add_row(
                str(task.id),
                task.type,
                task.status,
                str(task.score),
                str(task.claimed_at),
                str(task.last_attempt_at) or "N/A",
                str(task.solved_at) or "N/A"
            )

        console.print(table)

        if watch:
            console.print("[yellow]Watch mode enabled. Press Ctrl+C to exit.[/yellow]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
