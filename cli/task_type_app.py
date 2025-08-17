import typer
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in
from typing import Optional
from rich.table import Table
from cli.formatter import print_as_json
from api_models import RoundTaskTypeCreateRequest, RoundTaskType

task_type_app = typer.Typer(help="Task type management")


def display_task_type_details(task_type: RoundTaskType, success_message: str, json: bool) -> None:
    if json:
        return print_as_json(task_type)

    console.print(success_message)
    console.print(f"[bold]Type:[/bold] {task_type.type}")
    console.print(f"[bold]Round ID:[/bold] {task_type.round_id}")
    console.print(
        f"[bold]Max Tasks Per Team:[/bold] "
        f"{task_type.max_tasks_per_team if task_type.max_tasks_per_team is not None else 'N/A'}"
    )
    console.print(f"[bold]Time to Solve:[/bold] {task_type.time_to_solve} minutes")
    console.print(f"[bold]Generator URL:[/bold] {task_type.generator_url}")

    return None


@task_type_app.command("list")
def task_type_list(
    round_id: int = typer.Option(..., "--round", "-r", help="Round ID"),
    json: bool = json_output_option
) -> None:
    """List all task types for a round."""
    ensure_logged_in()

    task_types = api_client.get_round_task_types(round_id)

    if json:
        return print_as_json(task_types)

    table = Table(title=f"Task Types for Round {round_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Type", max_width=15, overflow="ellipsis", no_wrap=True)
    table.add_column("Max Tasks Per Team")
    table.add_column("Time to Solve (min)")
    table.add_column("Generator URL")
    table.add_column("Generator Settings")

    for task_type in task_types:
        table.add_row(
            str(task_type.id),
            task_type.type,
            str(task_type.max_tasks_per_team) if task_type.max_tasks_per_team is not None else "N/A",
            str(task_type.time_to_solve),
            task_type.generator_url,
            task_type.generator_settings if task_type.generator_settings else "N/A"
        )

    console.print(table)
    return None


@task_type_app.command("show")
def task_type_show(
    task_type_id: int = typer.Option(..., "--id", help="Task Type ID"),
    json: bool = json_output_option
) -> None:
    """Show details of a specific task type."""
    ensure_logged_in()

    task_type = api_client.get_round_task_type(task_type_id)

    if json:
        return print_as_json(task_type)

    console.print(f"[bold]Task Type ID:[/bold] {task_type.id}")
    console.print(f"[bold]Round ID:[/bold] {task_type.round_id}")
    console.print(f"[bold]Type:[/bold] {task_type.type}")
    console.print(
        f"[bold]Max Tasks Per Team:[/bold] "
        f"{task_type.max_tasks_per_team if task_type.max_tasks_per_team is not None else 'N/A'}"
    )
    console.print(f"[bold]Time to Solve:[/bold] {task_type.time_to_solve} minutes")
    console.print(f"[bold]Generator URL:[/bold] {task_type.generator_url}")
    console.print(
        f"[bold]Generator Settings:[/bold] "
        f"{task_type.generator_settings if task_type.generator_settings else 'N/A'}"
    )
    console.print(f"[bold]Generator Secret:[/bold] {'*' * 8} (hidden)")

    return None


@task_type_app.command("create")
def task_type_create(
    round_id: int = typer.Option(..., "--round", "-r", help="Round ID"),
    type_name: str = typer.Option(..., "--type", "-t", help="Task type name"),
    generator_url: str = typer.Option(..., "--generator-url", "-g", help="Generator URL"),
    generator_settings: Optional[str] = typer.Option(None, "--generator-settings", "-s", help="Gen settings (JSON)"),
    generator_secret: str = typer.Option(..., "--generator-secret", help="Generator secret"),
    max_tasks_per_team: Optional[int] = typer.Option(None, "--max-tasks", "-m", help="Maximum tasks per team"),
    time_to_solve: int = typer.Option(60, "--time-to-solve", help="Time limit to solve the task in min (def: 60)"),
    json: bool = json_output_option
) -> None:
    """Create a new task type."""
    ensure_logged_in()

    task_type_data = RoundTaskTypeCreateRequest(
        round_id=round_id,
        type=type_name,
        generator_url=generator_url,
        generator_settings=generator_settings,
        generator_secret=generator_secret,
        max_tasks_per_team=max_tasks_per_team,
        time_to_solve=time_to_solve
    )

    task_type = api_client.create_round_task_type(task_type_data)

    display_task_type_details(
        task_type,
        f"[green]Task type created successfully with ID: {task_type.id}[/green]",
        json,
    )

    return None


@task_type_app.command("update")
def task_type_update(
    task_type_id: int = typer.Option(..., "--id", help="Task Type ID"),
    type_name: Optional[str] = typer.Option(None, "--type", "-t", help="Task type name"),
    generator_url: Optional[str] = typer.Option(None, "--generator-url", "-g", help="Generator URL"),
    generator_settings: Optional[str] = typer.Option(None, "--generator-settings", "-s", help="Gen settings (JSON)"),
    generator_secret: Optional[str] = typer.Option(None, "--generator-secret", help="Generator secret"),
    max_tasks_per_team: Optional[int] = typer.Option(None, "--max-tasks", "-m", help="Maximum tasks per team"),
    time_to_solve: Optional[int] = typer.Option(None, "--time-to-solve", help="Time limit to solve the task in min"),
    json: bool = json_output_option
) -> None:
    """Update an existing task type."""
    ensure_logged_in()

    current_task_type = api_client.get_round_task_type(task_type_id)

    task_type_data = RoundTaskTypeCreateRequest(
        round_id=current_task_type.round_id,
        type=type_name if type_name is not None else current_task_type.type,
        generator_url=generator_url if generator_url is not None else current_task_type.generator_url,
        generator_settings=generator_settings if generator_settings is not None else current_task_type.generator_settings,
        generator_secret=generator_secret if generator_secret is not None else current_task_type.generator_secret,
        max_tasks_per_team=max_tasks_per_team if max_tasks_per_team is not None else current_task_type.max_tasks_per_team,
        time_to_solve=time_to_solve if time_to_solve is not None else current_task_type.time_to_solve
    )

    task_type = api_client.update_round_task_type(task_type_id, task_type_data)

    display_task_type_details(
        task_type,
        f"[green]Task type updated successfully with ID: {task_type.id}[/green]",
        json,
    )

    return None


@task_type_app.command("delete")
def task_type_delete(
    task_type_id: int = typer.Option(..., "--id", help="Task Type ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json: bool = json_output_option
) -> None:
    """Delete a task type."""
    ensure_logged_in()

    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to delete task type with ID {task_type_id}?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return None

    result = api_client.delete_round_task_type(task_type_id)

    if json:
        return print_as_json(result)

    console.print(f"[green]Task type with ID {task_type_id} deleted successfully.[/green]")

    return None