#!/usr/bin/env python3
import logging
import sys

from cli.typers.board_app import board_app
from cli.typers.round_app import round_app
from cli.typers.task_app import task_app
from cli.typers.team_app import team_app
from cli.typers.challenge_app import app

__all__ = ["app"]

app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(board_app, name="board")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # nuke prior handlers so this actually applies
    )

    app()
