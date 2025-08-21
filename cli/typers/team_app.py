import csv
import typer
from rich.table import Table

from api_models import TeamsImportRequest, Team
from cli.typers.app_deps import api_client, json_output_option, console, ensure_logged_in
from cli.formatter import print_as_json

team_app = typer.Typer(help="Team management commands", no_args_is_help=True)


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


@team_app.command("list")

def team_list(
    challenge_id: str = typer.Argument(None, help="Challenge ID"),
    as_json: bool = json_output_option
) -> None:
    """List teams for the specified or current challenge."""
    ensure_logged_in()
    teams = api_client.get_teams(challenge_id)

    if as_json:
        return print_as_json(teams)

    table = Table(title=f"Teams for challenge '{challenge_id or 'current'}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Members")
    table.add_column("Captain Contact")
    table.add_column("API Key", style="magenta")

    for t in teams:
        table.add_row(str(t.id), str(t.name), str(t.members), str(t.captain_contact), str(t.api_key))

    console.print(table)
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
