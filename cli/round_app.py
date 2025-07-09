import typer
from app_deps import api_client, json_output_option, console, ensure_logged_in
from typing import Optional
from rich.table import Table
from formatter import print_as_json

round_app = typer.Typer(help="Round management commands")

# Round commands
@round_app.command("show")
def round_show(
    round_id: Optional[int] = typer.Option(None, "--round", "-r", help="Round ID"),
    json: bool = json_output_option
):
    """Show round information."""
    ensure_logged_in()

    try:
        # Get round info from the API
        round_info = api_client.get_round_info(round_id)

        # If json flag is set, the decorator will handle the output
        if json:
            return print_as_json(round_info)

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


@round_app.command("publish")
def round_publish(
    round_id: int = typer.Argument(..., help="Round ID to publish")
):
    """Publishes a round so that players can see it."""
    ensure_logged_in()

    try:
        # Publishes the round via the API
        round_info = api_client.publish_round(round_id)

        # Displays the success of the message
        console.print(f"[green]Round published: Round {round_info.index} (Challenge {round_info.challenge_id}), ID: {round_id}[/green]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@round_app.command("list")
def round_list(json: bool = json_output_option):
    """List all rounds."""
    ensure_logged_in()

    try:
        # Get rounds from the API
        rounds = api_client.list_rounds()

        # If json flag is set, the decorator will handle the output
        if json:
            return print_as_json(rounds)

        # Otherwise, format the data for human-readable output
        table = Table(title="Rounds")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Start Time")
        table.add_column("End Time")

        for round_info in rounds.rounds:
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


@round_app.command("update")
def round_update(
    round_id: int = typer.Option(..., "--round", "-r", help="Round ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Round status (draft, active, completed)"),
    start_time: Optional[str] = typer.Option(None, "--start-time", help="Start time (ISO format)"),
    end_time: Optional[str] = typer.Option(None, "--end-time", help="End time (ISO format)"),
    claim_by_type: Optional[bool] = typer.Option(None, "--claim-by-type", help="Allow claiming tasks by type"),
    allow_resubmit: Optional[bool] = typer.Option(None, "--allow-resubmit", help="Allow resubmitting answers"),
    score_decay: Optional[str] = typer.Option(None, "--score-decay", help="Score decay type"),
    json: bool = json_output_option
):
    """Update round information."""
    ensure_logged_in()

    try:
        # Build update data dictionary with only provided fields
        update_data = {}
        if status is not None:
            update_data["status"] = status
        if start_time is not None:
            update_data["start_time"] = start_time
        if end_time is not None:
            update_data["end_time"] = end_time
        if claim_by_type is not None:
            update_data["claim_by_type"] = claim_by_type
        if allow_resubmit is not None:
            update_data["allow_resubmit"] = allow_resubmit
        if score_decay is not None:
            update_data["score_decay"] = score_decay

        # If no fields were provided, show an error
        if not update_data:
            console.print("[red]Error: At least one field to update must be provided[/red]")
            raise typer.Exit(1)

        # Update round info via the API
        round_info = api_client.update_round(round_id, update_data)

        # If json flag is set, the decorator will handle the output
        if json:
            return print_as_json(round_info)

        # Otherwise, format the data for human-readable output
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
):
    """Delete a round."""
    ensure_logged_in()

    try:
        # Get round info to show what will be deleted
        round_info = api_client.get_round_info(round_id)

        # If not confirmed, ask for confirmation
        if not confirm:
            console.print(f"[bold yellow]Warning: You are about to delete Round {round_id}[/bold yellow]")
            console.print(f"Status: {round_info.status}")
            console.print(f"Start Time: {round_info.start_time}")
            console.print(f"End Time: {round_info.end_time}")

            # Ask for confirmation
            confirmed = typer.confirm("Are you sure you want to delete this round?")
            if not confirmed:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return None

        # Delete the round
        result = api_client.delete_round(round_id)

        # If json flag is set, print the result as JSON
        if json:
            return print_as_json(result)

        # Otherwise, print a success message
        console.print(f"[bold green]Round {round_id} deleted successfully![/bold green]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)