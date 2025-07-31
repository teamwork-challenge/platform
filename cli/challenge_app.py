#!/usr/bin/env python3
from typing import Optional

import typer
from rich.markdown import Markdown

from app_deps import api_client, console, ensure_logged_in, json_output_option
from formatter import print_as_json
from api_models.models import ChallengeUpdateRequest

app = typer.Typer(help="Teamwork Challenge CLI", pretty_exceptions_short=True, pretty_exceptions_show_locals=False)

# Authentication commands
@app.command()
def login(api_key: str):
    """Store API key into config file after successful login."""
    api_client.save_api_key(api_key)
    role = api_client.auth()
    console.print(f"[green]Successfully logged in with role {role} using API key: {api_key}[/green]")
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
    print_challenge(challenge)

    return None


@app.command("update")
def update(
    challenge_id: int = typer.Option(..., "--challenge-id", "-c", help="Challenge ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Challenge title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Challenge description"),
    current_round_id: Optional[int] = typer.Option(None, "--current-round", "-r", help="Current round ID"),
    do_delete: Optional[bool] = typer.Option(None, "--delete", help="delete challenge"),
    undo_delete: Optional[bool] = typer.Option(None, "--undelete", help="undelete challenge"),
    as_json: bool = json_output_option
):
    """Update challenge information."""
    ensure_logged_in()

    # Build update data dictionary with only provided fields
    update_data = ChallengeUpdateRequest()
    update_data.title = title
    update_data.description = description
    update_data.current_round_id = current_round_id
    if do_delete:
        update_data.deleted = True
    if undo_delete:
        update_data.deleted = False

    # If no fields were provided, show an error
    if not update_data:
        console.print("[red]Error: At least one field to update must be provided[/red]")
        raise typer.Exit(1)

    # Update challenge info via the API
    challenge = api_client.update_challenge(challenge_id, update_data)

    # If json flag is set, the decorator will handle the output
    if as_json:
        return print_as_json(challenge)

    console.print("[bold green]Challenge updated successfully![/bold green]")
    print_challenge(challenge)


@app.command("delete")
def delete(
    challenge_id: int = typer.Option(..., "--challenge-id", "-c", help="Challenge ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    as_json: bool = json_output_option
):
    """Mark a challenge as deleted."""
    ensure_logged_in()

    # Get challenge info to show what will be deleted
    challenge = api_client.get_challenge_info(challenge_id)

    # If not confirmed, ask for confirmation
    if not confirm:
        console.print(f"[bold yellow]Warning: You are about to mark Challenge {challenge_id} as deleted[/bold yellow]")
        console.print(f"Title: {challenge.title}")

        # Ask for confirmation
        confirmed = typer.confirm("Are you sure you want to mark this challenge as deleted?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return None

    # Mark the challenge as deleted
    result = api_client.delete_challenge(challenge_id)

    # If json flag is set, print the result as JSON
    if as_json:
        return print_as_json(result)

    # Otherwise, print a success message
    console.print(f"[bold green]Challenge {challenge_id} marked as deleted successfully![/bold green]")


def print_challenge(challenge):
    console.print(f"[bold blue]Challenge {challenge.id}[/bold blue]")
    console.print(f"Name: {challenge.title}")
    console.print(f"Current Round: {challenge.current_round_id}")
    if challenge.deleted:
        console.print("[bold red]This challenge is marked as deleted.[/bold red]")
    console.print()
    console.print(Markdown(challenge.description))