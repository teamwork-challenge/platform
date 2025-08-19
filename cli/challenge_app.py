#!/usr/bin/env python3
from typing import Optional

import hjson
import typer
from rich.markdown import Markdown
from rich.table import Table

from api_models import Challenge
from cli.app_deps import api_client, console, ensure_logged_in, json_output_option
from cli.formatter import print_as_json

app = typer.Typer(help="Teamwork Challenge CLI", pretty_exceptions_short=True, pretty_exceptions_show_locals=False)


# Authentication commands
@app.command()
def login(api_key: str) -> None:
    """Store an API key into the config file after successful login."""
    # Save the API key and verify it's valid by calling /auth.
    # If verification fails, remove the key and re-raise the error so tests can catch it.
    api_client.save_api_key(api_key)
    try:
        role = api_client.auth()
    except Exception:
        # Revert saved invalid key
        api_client.remove_api_key()
        raise
    console.print(f"[green]Successfully logged in with role {role} using API key: {api_key}[/green]")


@app.command()
def logout() -> None:
    """Remove an API key from the config file."""
    api_client.remove_api_key()
    console.print("[green]Successfully logged out[/green]")


@app.command("list")
def list_challenges(as_json: bool = json_output_option) -> None:
    """List all challenges."""
    ensure_logged_in()
    challenges = api_client.get_challenges()

    if as_json:
        return print_as_json(challenges)

    table = Table(title="Challenges")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Current Round")

    for ch in challenges:
        table.add_row(str(ch.id), str(ch.title), str(ch.current_round_id))

    console.print(table)
    return None


@app.command("show")
def show(
    challenge_id: Optional[str] = typer.Option(None, "--challenge-id", "-c", help="Challenge ID"),
    as_json: bool = json_output_option
) -> None:
    """Show challenge information."""
    ensure_logged_in()

    challenge = api_client.get_challenge_info(challenge_id)

    if as_json:
        return print_as_json(challenge)

    print_challenge(challenge)

    return None


@app.command("update")
def update(challenge_hjson_path: str = typer.Argument(..., help="Challenge HJSON file path")) -> None:
    """Update challenge information."""
    ensure_logged_in()
    with open(challenge_hjson_path) as f:
        challenge_hjson = hjson.load(f)
    challenge = Challenge.model_validate(challenge_hjson)
    challenge = api_client.put_challenge(challenge)
    return print_as_json(challenge)


@app.command("teams")
def list_teams(
    challenge_id: Optional[str] = typer.Option(None, "--challenge", "-c", help="Challenge ID"),
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

    for t in teams:
        table.add_row(str(t.id), str(t.name), str(t.members), str(t.captain_contact))

    console.print(table)
    return None


def print_challenge(challenge: Challenge) -> None:
    console.print(f"[bold blue]Challenge {challenge.id}[/bold blue]")
    console.print(f"Name: {challenge.title}")
    console.print(f"Current Round: {challenge.current_round_id}")
    console.print()
    console.print(Markdown(challenge.description))