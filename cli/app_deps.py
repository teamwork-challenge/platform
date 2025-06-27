import typer
from pathlib import Path
from rich.console import Console
from api_client import ApiClient

json_output_option = typer.Option(False, "--json", is_flag=True, help="Output in JSON format", )
console = Console()
CONFIG_PATH = Path.home() / ".challenge" / "config.json"
api_client = ApiClient()
