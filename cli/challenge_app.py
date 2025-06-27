#!/usr/bin/env python3
import typer
from rich.markdown import Markdown
from app_deps import api_client, console
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
def show(as_json: bool = False):
    """Show challenge information."""
    if not api_client.api_key:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    # Get challenge info from the API
    challenge = api_client.get_challenge_info()

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
