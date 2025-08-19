import typer
from pathlib import Path
from rich.console import Console
from cli.api_client import ApiClient
from cli.config_manager import ConfigManager

json_output_option = typer.Option(False, "--json", help="Output in JSON format")
console = Console(width=120)
CONFIG_PATH = Path.home() / ".challenge" / "config.json"
config_manager = ConfigManager(CONFIG_PATH)
api_client = ApiClient(config_manager)


def ensure_logged_in() -> None:
    if config_manager.get_api_key() is None:
        console.print("[red]Not logged in. Use 'challenge login <API_KEY>' to log in.[/red]")
        raise typer.Exit(1)