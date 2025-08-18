import typer
from cli.app_deps import api_client, json_output_option, console, ensure_logged_in
from cli.formatter import print_as_json

team_app = typer.Typer(help="Team management commands")


# Team commands
@team_app.command("show")
def team_show(as_json: bool = json_output_option) -> None:
    """Show team information."""
    ensure_logged_in()

    team = api_client.get_team_info()

    if as_json:
        return print_as_json(team)

    console.print("[bold]Team Information:[/bold]")
    console.print(f"Team ID: {team.id}")
    console.print(f"Team Name: {team.name}")
    console.print(f"Members: {team.members}")
    console.print(f"Challenge ID: {team.challenge_id}")

    return None


@team_app.command("rename")
def team_rename(new_name: str = typer.Argument(..., help="New team name"),
                as_json: bool = json_output_option) -> None:
    """Rename team (allowed until first submission)."""
    ensure_logged_in()

    team = api_client.rename_team(new_name)

    if as_json:
        return print_as_json(team)

    console.print(f"[green]Team renamed to: {team.name}[/green]")

    return None
