from typing import Optional

import hjson
import typer
from rich.table import Table

from api_models import Round
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in
from cli.formatter import print_as_json

round_app = typer.Typer(help="Round management commands")


def print_round(round_info: Round) -> None:
    console.print(f"RoundID: {round_info.id}")
    if not round_info.published:
        console.print(f"NOT PUBLISHED")
    console.print(f"ChallengeID: {round_info.challenge_id}")
    console.print(f"Start Time: {round_info.start_time}")
    console.print(f"End Time: {round_info.end_time}")
    console.print(f"Claim by Type: {round_info.claim_by_type}")
    if round_info.task_types is None:
        return
    task_types_table = Table(title="Task Types")
    task_types_table.add_column("Type")
    task_types_table.add_column("Task Count")
    task_types_table.add_column("Time To Solve")
    task_types_table.add_column("Score")
    for task_type in round_info.task_types:
        task_types_table.add_row(
            task_type.type,
            str(task_type.n_tasks),
            str(task_type.time_to_solve),
            str(task_type.score)
        )
    console.print(task_types_table)


# Round commands
@round_app.command("show")
def round_show(
    challenge_id: Optional[str] = typer.Option(None, "--challenge", "-c", help="Challenge ID"),
    round_id: Optional[str] = typer.Option(None, "--round", "-r", help="Round ID"),
    json: bool = json_output_option
) -> None:
    """Show round information."""
    ensure_logged_in()

    round_info = api_client.get_round(challenge_id, round_id)
    #round_info.task_types = api_client.get_round_task_types(round_id)

    if json:
        return print_as_json(round_info)

    print_round(round_info)

    return None


@round_app.command("list")
def round_list(
    challenge_id: Optional[str] = typer.Option(None, "--challenge", "-c", help="Challenge ID"),
    json: bool = json_output_option
) -> None:
    """List all rounds for a challenge."""
    ensure_logged_in()

    rounds = api_client.list_rounds(challenge_id)

    if json:
        return print_as_json(rounds)

    table = Table(title="Rounds")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Published", style="green")
    table.add_column("Start Time")
    table.add_column("End Time")

    for round_info in rounds:
        table.add_row(
            "Round " + str(round_info.id),
            str(round_info.published),
            str(round_info.start_time),
            str(round_info.end_time)
        )

    console.print(table)
    return None


@round_app.command("update")
def round_update(round_hjson_path: str = typer.Argument(..., help="Round HJSON file path")) -> None:
    """Update round information."""
    ensure_logged_in()
    with open(round_hjson_path) as f:
        round_hjson = hjson.load(f)
    round = Round.model_validate(round_hjson)
    round = api_client.update_round(round)
    return print_as_json(round)


@round_app.command("delete")
def round_delete(
    round_id: str = typer.Option(..., "--round", "-r", help="Round ID"),
    challenge_id: str = typer.Option(..., "--challenge", "-c", help="Challenge ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json: bool = json_output_option
) -> None:
    """Delete a round."""
    ensure_logged_in()


    if not confirm:
        console.print(f"[bold yellow]Warning: You are about to delete Round {round_id}[/bold yellow]")

        confirmed = typer.confirm("Are you sure you want to delete this round?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return None

    result = api_client.delete_round(challenge_id, round_id)

    if json:
        return print_as_json(result)

    console.print(f"[bold green]Round {round_id} deleted successfully![/bold green]")

    return None
