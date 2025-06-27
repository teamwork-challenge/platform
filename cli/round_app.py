import typer
from app_deps import api_client, json_output_option, console
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
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

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


@round_app.command("list")
def round_list(json: bool = json_output_option):
    """List all rounds."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

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

