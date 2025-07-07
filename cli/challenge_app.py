#!/usr/bin/env python3
from typing import Optional

import typer
from rich.markdown import Markdown
from app_deps import api_client, console, ensure_logged_in, json_output_option
from formatter import print_as_json

app = typer.Typer(help="Teamwork Challenge CLI", pretty_exceptions_short=True, pretty_exceptions_show_locals=False)

# Authentication commands
@app.command()
def login(api_key: str):
    """Store API key into config file after successful login."""
    api_client.save_api_key(api_key)
    api_client.get_team_info()
    console.print(f"[green]Successfully logged in with API key: {api_key}[/green]")
    return None


@app.command()
def logout():
    """Remove API key from config file."""
    api_client.remove_api_key()
    console.print("[green]Successfully logged out[/green]")


@app.command("show")
def show(challenge_id: Optional[int] = typer.Option(None, "--challenge-id", "-c", help="Challenge ID"), as_json: bool = json_output_option):
    """Show challenge information."""
    ensure_logged_in()

    # Get challenge info from the API
    challenge = api_client.get_challenge_info(challenge_id)

    # If json flag is set, the decorator will handle the output
    if as_json:
        return print_as_json(challenge)

    # Otherwise, format the data for human-readable output
    console.print("[bold]Challenge Information:[/bold]")
    console.print(f"Name: {challenge.title}")
    console.print(f"Current Round: {challenge.current_round_id}")
    console.print()
    console.print(Markdown(challenge.description))

    return None
