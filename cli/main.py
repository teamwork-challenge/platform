#!/usr/bin/env python3
from board_app import board_app
from round_app import round_app
from task_app import task_app
from team_app import team_app
from challenge_app import app

app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(board_app, name="board")

if __name__ == "__main__":
    app()
