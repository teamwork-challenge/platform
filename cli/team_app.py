import typer
from app_deps import api_client, json_output_option, console
from formatter import print_as_json

team_app = typer.Typer(help="Team management commands")

# Team commands
@team_app.command("show")
def team_show(as_json: bool = json_output_option):
    """Show team information."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Get team info from the API
        team = api_client.get_team_info()

        # If json flag is set, the decorator will handle the output
        if as_json:
            return print_as_json(team)

        # Otherwise, format the data for human-readable output
        console.print("[bold]Team Information:[/bold]")
        console.print(f"Team ID: {team.id}")
        console.print(f"Team Name: {team.name}")
        console.print(f"Members: {team.members}")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@team_app.command("rename")
def team_rename(new_name: str, as_json: bool = json_output_option):
    """Rename team (allowed until first submission)."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    try:
        # Rename team using the API
        team = api_client.rename_team(new_name)

        # If json flag is set, the decorator will handle the output
        if as_json:
            return print_as_json(team)

        # Otherwise, format the data for human-readable output
        console.print(f"[green]Team renamed to: {team.name}[/green]")

        return None
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
