from typing import Any

from pydantic import BaseModel
from rich.console import Console
import json

from rich.table import Table


def print_as_json(obj: Any) -> None:
    d = obj
    if isinstance(obj, BaseModel):
        d = obj.model_dump_json(indent=2)
    else:
        d = json.dumps(d, indent=2)
    Console().print(d)

def as_table(obj: Any) -> Table:
    table = Table(title=type(obj).__name__)
    table.add_column("Field", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="left", style="magenta")
    if isinstance(obj, BaseModel):
        d = obj.model_dump()
    elif hasattr(obj, '__dict__'):
        d = vars(obj)
    else:
        d = obj
    for key, value in d.items():
        table.add_row(str(key), str(value) if value is not None else "None")
    return table


def pretty_print(obj: Any, as_json: bool = False) -> None:
    if as_json:
        print_as_json(obj)
    else:
        Console().print(as_table(obj))
