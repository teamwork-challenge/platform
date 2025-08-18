#!/usr/bin/env python3
import typer
from cli.board_app import board_app
from cli.round_app import round_app
from cli.task_app import task_app
from cli.task_type_app import task_type_app
from cli.team_app import team_app
from cli.challenge_app import app

__all__ = ["app"]

app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(task_type_app, name="task-type")
app.add_typer(board_app, name="board")

if __name__ == "__main__":
    app()
