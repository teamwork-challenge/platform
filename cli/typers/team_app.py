import csv
import typer
from api_models import TeamsImportRequest
from cli.typers.app_deps import api_client, json_output_option, console, ensure_logged_in
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


@team_app.command("create")
def team_create(
        challenge_id: str,
        teams_tsv_path: str = typer.Argument(..., help="Path to a tab-separated file with the header: 'name\tmembers\tcaptain_contact'")) -> None:
    """Create teams for a challenge using a TSV file (batch import)."""
    ensure_logged_in()

    with open(teams_tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        teams = list(reader)

    request = TeamsImportRequest.model_validate({"challenge_id": challenge_id, "teams": teams})
    response = api_client.create_teams(request)
    return print_as_json(response)
