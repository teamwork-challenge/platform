#!/usr/bin/env python3
from typing import Optional

import hjson
import typer
from rich.markdown import Markdown
from rich.table import Table

from api_models import Challenge
from cli.typers.app_deps import api_client, console, ensure_logged_in, json_output_option
from cli.formatter import print_as_json

# Root app is defined in cli.main; this module defines the 'challenge' sub-typer
challenge_app = typer.Typer(help="Challenge management commands", pretty_exceptions_short=True, pretty_exceptions_show_locals=False, no_args_is_help=True)


@challenge_app.command("list")
def challenge_list(as_json: bool = json_output_option) -> None:
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


@challenge_app.command("show")
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


@challenge_app.command("update")
def update(challenge_hjson_path: str = typer.Argument(..., help="Challenge HJSON file path")) -> None:
    """Update challenge information."""
    ensure_logged_in()
    with open(challenge_hjson_path) as f:
        challenge_hjson = hjson.load(f)
    challenge = Challenge.model_validate(challenge_hjson)
    challenge = api_client.put_challenge(challenge)
    return print_as_json(challenge)


def print_challenge(challenge: Challenge) -> None:
    console.print(f"[bold blue]Challenge {challenge.id}[/bold blue]")
    console.print(f"Name: {challenge.title}")
    console.print(f"Current Round: {challenge.current_round_id}")
    console.print()
    console.print(Markdown(challenge.description))