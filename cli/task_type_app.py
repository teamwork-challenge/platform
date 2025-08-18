import typer
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in
from typing import Optional
from rich.table import Table
from cli.formatter import print_as_json
from api_models import RoundTaskType

task_type_app = typer.Typer(help="Task type management")


def display_task_type_details(task_type: RoundTaskType, success_message: str, json: bool) -> None:
    if json:
        return print_as_json(task_type)

    console.print(success_message)
    console.print(f"[bold]Type:[/bold] {task_type.type}")
    console.print(f"[bold]Amount of Tasks:[/bold] {task_type.n_tasks}"
    )
    console.print(f"[bold]Time to Solve:[/bold] {task_type.time_to_solve} minutes")
    console.print(f"[bold]Generator URL:[/bold] {task_type.generator_url}")

    return None


@task_type_app.command("list")
def task_type_list(
    round_id: str = typer.Argument(..., help="RoundID"),
    json: bool = json_output_option
) -> None:
    """List all task types for a round."""
    ensure_logged_in()

    task_types = api_client.get_round_task_types(round_id)

    if json:
        return print_as_json(task_types)

    table = Table(title=f"Task Types for Round {round_id}")
    table.add_column("Type")
    table.add_column("Task Count")
    table.add_column("Time")
    table.add_column("Score")

    for task_type in task_types:
        table.add_row(
            task_type.type,
            str(task_type.n_tasks) if task_type.n_tasks is not None else "N/A",
            str(task_type.time_to_solve),
            str(task_type.score)
        )

    console.print(table)
    return None
