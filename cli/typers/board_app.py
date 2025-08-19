import typer
from cli.typers.app_deps import api_client, json_output_option, console
from typing import Optional
from rich.table import Table
from cli.formatter import print_as_json

board_app = typer.Typer(help="Leaderboards and dashboards")


# Board commands
@board_app.command("dashboard")
def board_dashboard(
    round_id: Optional[str] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = json_output_option
) -> None:
    """Show a dashboard with task statistics."""
    if not api_client.logged_in():
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    dashboard = api_client.get_dashboard(round_id)

    # If a JSON flag is set, the decorator will handle the output
    if json:
        return print_as_json(dashboard)

    # Otherwise, format the data for human-readable output
    table = Table(title=f"Dashboard for Round {dashboard.round_id}")
    table.add_column("Task Type", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("PENDING", justify="right")
    table.add_column("AC", justify="right")
    table.add_column("WA", justify="right")
    table.add_column("Remaining", justify="right")

    for task_type, type_stats in dashboard.stats.items():
        if task_type != 'total':  # Handle total separately
            table.add_row(
                task_type,
                str(type_stats.total),
                str(type_stats.pending),
                str(type_stats.ac),
                str(type_stats.wa),
                str(type_stats.remaining)
            )

    # Add a total row if available
    if 'total' in dashboard.stats:
        total_stats = dashboard.stats['total']
        table.add_row(
            "Total",
            str(total_stats.total),
            str(total_stats.pending),
            str(total_stats.ac),
            str(total_stats.wa),
            str(total_stats.remaining)
        )

    console.print(table)

    if watch:
        console.print("[yellow]Watch mode is not implemented yet.[/yellow]")

    return None


@board_app.command("leaderboard")
def board_leaderboard(
    round_id: Optional[str] = typer.Option(None, "--round", "-r", help="Round ID"),
    watch: bool = typer.Option(False, "--watch", help="Watch for updates"),
    json: bool = json_output_option
) -> None:
    """Show a leaderboard with team scores."""
    if not api_client.logged_in():
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)

    leaderboard = api_client.get_leaderboard(round_id)

    if json:
        return print_as_json(leaderboard)

    table = Table(title=f"Leaderboard for Round {leaderboard.round_id}")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Team")
    table.add_column("General", justify="right")
    table.add_column("Math", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Total", justify="right", style="green")

    for team in leaderboard.teams:
        table.add_row(
            str(team.rank),
            team.name,
            str(team.scores.get('general', 'N/A')),
            str(team.scores.get('math', 'N/A')),
            str(team.scores.get('coding', 'N/A')),
            str(team.total_score)
        )

    console.print(table)

    if watch:
        console.print("[yellow]Watch mode is not implemented yet.[/yellow]")

    return None