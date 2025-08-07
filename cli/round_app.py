import typer
from typing import Optional
from rich.table import Table
from datetime import datetime
from api_models import RoundCreateRequest, RoundStatus, RoundUpdateRequest
from cli.formatter import print_as_json
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in

round_app = typer.Typer(help="Round management commands")

# Round commands
@round_app.command("show")
def round_show(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    json: bool = json_output_option
) -> None:
    """Show round information."""
    ensure_logged_in()

    try:
        round_info = api_client.get_round_info(round_id)

        if json:
            return print_as_json(round_info)

        console.print(f"[bold]Round {round_info.id} Information:[/bold]")
        console.print(f"Status: {round_info.status}")
        console.print(f"Start Time: {round_info.start_time}")
        console.print(f"End Time: {round_info.end_time}")
        console.print(f"Claim by Type: {round_info.claim_by_type}")
        console.print(f"Allow Resubmit: {round_info.allow_resubmit}")
        console.print(f"Score Decay: {round_info.score_decay}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("publish")
def round_publish(
    round_id: int = typer.Argument(..., help="Round ID to publish")
) -> None:
    """Publishes a round so that players can see it."""
    ensure_logged_in()

    try:
        round_info = api_client.publish_round(round_id)

        console.print(f"[green]Round published: Round {round_info.index} (Challenge {round_info.challenge_id}), ID: {round_id}[/green]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("create")
def round_create(
    challenge_id: int = typer.Option(..., "--challenge", "-c", help="Challenge ID"),
    index: int = typer.Option(..., "--index", "-i", help="Round index within the challenge"),
    start_time: str = typer.Option(..., "--start-time", help="Start time (ISO format)"),
    end_time: str = typer.Option(..., "--end-time", help="End time (ISO format)"),
    claim_by_type: bool = typer.Option(False, "--claim-by-type", help="Allow claiming tasks by type"),
    allow_resubmit: bool = typer.Option(False, "--allow-resubmit", help="Allow resubmitting answers"),
    score_decay: str = typer.Option("no", "--score-decay", help="Score decay type"),
    status: str = typer.Option("draft", "--status", "-s", help="Round status (draft, published)"),
    json: bool = json_output_option
) -> None:
    """Create a new round."""
    ensure_logged_in()

    try:

        # Parse the datetime strings
        start_time_dt = datetime.fromisoformat(start_time)
        end_time_dt = datetime.fromisoformat(end_time)
        
        round_data = RoundCreateRequest(
            challenge_id=challenge_id,
            index=index,
            start_time=start_time_dt,
            end_time=end_time_dt,
            claim_by_type=claim_by_type,
            allow_resubmit=allow_resubmit,
            score_decay=score_decay,
            status=RoundStatus(status)
        )

        round_info = api_client.create_round(round_data)

        if json:
            return print_as_json(round_info)

        console.print(f"[bold green]Round created successfully![/bold green]")
        console.print(f"Round ID: {round_info.id}")
        console.print(f"Challenge ID: {round_info.challenge_id}")
        console.print(f"Index: {round_info.index}")
        console.print(f"Status: {round_info.status}")
        console.print(f"Start Time: {round_info.start_time}")
        console.print(f"End Time: {round_info.end_time}")
        console.print(f"Claim by Type: {round_info.claim_by_type}")
        console.print(f"Allow Resubmit: {round_info.allow_resubmit}")
        console.print(f"Score Decay: {round_info.score_decay}")
        
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("list")
def round_list(
    challenge_id: Optional[int] = typer.Option(None, "--challenge", "-c", help="Challenge ID"),
    json: bool = json_output_option
) -> None:
    """List all rounds for a challenge."""
    ensure_logged_in()

    try:
        rounds = api_client.list_rounds(challenge_id)

        if json:
            return print_as_json(rounds)

        table = Table(title="Rounds")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Start Time")
        table.add_column("End Time")

        for round_info in rounds.rounds:
            table.add_row(
                "Round " + str(round_info.id),
                str(round_info.index),
                round_info.status,
                str(round_info.start_time),
                str(round_info.end_time)
            )

        console.print(table)
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("update")
def round_update(
    round_id: int = typer.Option(..., "--round", "-r", help="Round ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Round status (draft, active, completed)"),
    start_time: Optional[str] = typer.Option(None, "--start-time", help="Start time (ISO format)"),
    end_time: Optional[str] = typer.Option(None, "--end-time", help="End time (ISO format)"),
    claim_by_type: Optional[str] = typer.Option(None, "--claim-by-type", help="Allow claiming tasks by type"),
    allow_resubmit: Optional[str] = typer.Option(None, "--allow-resubmit", help="Allow resubmitting answers"),
    score_decay: Optional[str] = typer.Option(None, "--score-decay", help="Score decay type"),
    json: bool = json_output_option
) -> None:
    """Update round information."""
    ensure_logged_in()

    try:
        # Build update data dictionary with only provided fields
        update_data = RoundUpdateRequest()
        if status is not None:
            update_data.status = RoundStatus(status)
        if start_time is not None:
            update_data.start_time = datetime.fromisoformat(start_time)
        if end_time is not None:
            update_data.end_time = datetime.fromisoformat(end_time)
        if claim_by_type is not None:
            update_data.claim_by_type = claim_by_type.lower() in ["true", "1", "yes", "y"]
        if allow_resubmit is not None:
            update_data.allow_resubmit = allow_resubmit.lower() in ["true", "1", "yes", "y"]
        if score_decay is not None:
            update_data.score_decay = score_decay

        round_info = api_client.update_round(round_id, update_data)

        if json:
            return print_as_json(round_info)

        console.print(f"[bold green]Round {round_info.id} updated successfully![/bold green]")
        console.print(f"Status: {round_info.status}")
        console.print(f"Start Time: {round_info.start_time}")
        console.print(f"End Time: {round_info.end_time}")
        console.print(f"Claim by Type: {round_info.claim_by_type}")
        console.print(f"Allow Resubmit: {round_info.allow_resubmit}")
        console.print(f"Score Decay: {round_info.score_decay}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("delete")
def round_delete(
    round_id: int = typer.Option(..., "--round", "-r", help="Round ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json: bool = json_output_option
) -> None:
    """Delete a round."""
    ensure_logged_in()

    try:
        round_info = api_client.get_round_info(round_id)

        if not confirm:
            console.print(f"[bold yellow]Warning: You are about to delete Round {round_id}[/bold yellow]")
            console.print(f"Status: {round_info.status}")
            console.print(f"Start Time: {round_info.start_time}")
            console.print(f"End Time: {round_info.end_time}")

            confirmed = typer.confirm("Are you sure you want to delete this round?")
            if not confirmed:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return None

        result = api_client.delete_round(round_id)

        if json:
            return print_as_json(result)

        console.print(f"[bold green]Round {round_id} deleted successfully![/bold green]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

        raise typer.Exit(1)
