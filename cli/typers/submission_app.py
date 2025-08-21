import typer
from typing import Optional
from rich.table import Table

from cli.typers.app_deps import api_client, json_output_option, console, ensure_logged_in
from cli.formatter import print_as_json

submission_app = typer.Typer(help="Submission-related commands")


@submission_app.command("list")
def list_submissions(task_id: str = typer.Option(..., "--task", "-t", help="Task ID"), json: bool = json_output_option) -> None:
    """List submissions for a specific task."""
    ensure_logged_in()
    subs = api_client.list_task_submissions(task_id)
    if json:
        return print_as_json(subs)

    if not subs:
        console.print("No submissions yet.")
        return None

    table = Table(title=f"Submissions for task {task_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Status")
    table.add_column("Score")
    table.add_column("Submitted At")
    for s in subs:
        table.add_row(str(s.id), str(s.status), str(s.score), str(s.submitted_at))
    console.print(table)
    return None


@submission_app.command("last")
def last_submission(team_id: Optional[str] = typer.Option(None, "--team", help="Team ID (admin only; players see their own)"), json: bool = json_output_option) -> None:
    """Show the last submission for a team in the current round."""
    ensure_logged_in()
    if team_id is None:
        # For players: server will use auth to check access when requesting explicit team_id
        from cli.typers.app_deps import config_manager
        # We don't know team id on client; require server-side check. Ask server for our own if None
        # Using placeholder 'me' not supported; force error if not provided by admin. For players, we need their team.
        # So just try fetching team info and use id
        try:
            me = api_client.get_team_info()
            team_id = me.id
        except Exception:
            team_id = ""
    if not team_id:
        console.print("[red]Team ID is required for admin or retrievable for player[/red]")
        raise typer.Exit(1)
    sub = api_client.last_submission_for_team(team_id)
    if json:
        return print_as_json(sub)
    console.print(f"Last submission for team {team_id}:")
    console.print(f"ID: {sub.id}")
    console.print(f"Status: {sub.status}")
    console.print(f"Score: {sub.score}")
    console.print(f"Submitted At: {sub.submitted_at}")
    return None


@submission_app.command("last-all")
def last_submission_all(json: bool = json_output_option) -> None:
    """List last submissions for all teams (admin only)."""
    ensure_logged_in()
    data = api_client.last_submission_for_all_teams()
    if json:
        return print_as_json(data)
    if not data:
        console.print("No submissions found")
        return None
    table = Table(title="Last submissions for all teams")
    table.add_column("Team ID", style="cyan")
    table.add_column("Submission ID")
    table.add_column("Status")
    table.add_column("Score")
    table.add_column("Submitted At")
    for item in data:
        team = str(item.get("team_id"))
        sub = item.get("submission") or {}
        table.add_row(team, str(sub.get("id")), str(sub.get("status")), str(sub.get("score")), str(sub.get("submitted_at")))
    console.print(table)
    return None
