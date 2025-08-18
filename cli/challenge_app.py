#!/usr/bin/env python3
from typing import Optional

import hjson
import typer
from rich.markdown import Markdown

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


@app.command("delete")
def delete(
    challenge_id: str = typer.Option(..., "--challenge-id", "-c", help="Challenge ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    as_json: bool = json_output_option
) -> None:
    """Mark a challenge as deleted."""
    ensure_logged_in()

    challenge = api_client.get_challenge_info(challenge_id)

    if not confirm:
        console.print(f"[bold yellow]Warning: You are about to mark Challenge {challenge_id} as deleted[/bold yellow]")
        console.print(f"Title: {challenge.title}")

        confirmed = typer.confirm("Are you sure you want to mark this challenge as deleted?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return None

    result = api_client.delete_challenge(challenge_id)

    if as_json:
        return print_as_json(result)

    console.print(f"[bold green]Challenge {challenge_id} marked as deleted successfully![/bold green]")

    return None


def print_challenge(challenge: Challenge) -> None:
    console.print(f"[bold blue]Challenge {challenge.id}[/bold blue]")
    console.print(f"Name: {challenge.title}")
    console.print(f"Current Round: {challenge.current_round_id}")
    console.print()
    console.print(Markdown(challenge.description))