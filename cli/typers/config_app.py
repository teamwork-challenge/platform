import typer

from cli.typers.app_deps import config_manager, console

config_app = typer.Typer(help="Configuration commands", no_args_is_help=True)


VALID_DESTINATIONS = {"file", "console"}
VALID_LEVELS = {"CRITICAL", "DEBUG", "INFO", "WARNING", "ERROR"}


@config_app.command("log-level")
def set_log_level(
    destination: str = typer.Argument(..., help="Destination: 'file' or 'console'"),
    level: str = typer.Argument(..., help="Level: CRITICAL, DEBUG, INFO, WARNING, ERROR"),
) -> None:
    """Set logging level for console or file and persist in config file."""
    dest = destination.lower()
    lvl = level.upper()

    if dest not in VALID_DESTINATIONS:
        console.print("[red]Invalid destination. Use 'file' or 'console'.[/red]")
        raise typer.Exit(code=2)
    if lvl not in VALID_LEVELS:
        console.print("[red]Invalid level. Use one of: NONE, DEBUG, INFO, WARNING, ERROR.[/red]")
        raise typer.Exit(code=2)

    # Persist
    log_cfg = config_manager.get("log_levels") or {}
    # Defaults if not present
    if "console" not in log_cfg:
        log_cfg["console"] = "NONE"
    if "file" not in log_cfg:
        log_cfg["file"] = "INFO"

    log_cfg[dest] = lvl
    config_manager.set("log_levels", log_cfg)

    console.print(f"[green]Set {dest} log level to {lvl}[/green]")


@config_app.command("api-url")
def set_api_url(url: str = typer.Argument(..., help="Base API URL, e.g., http://127.0.0.1:8088")) -> None:
    """Set or update the competition server address (base API URL)."""
    # Minimal validation: ensure something like scheme://host
    if "://" not in url:
        console.print("[yellow]Warning: URL has no scheme, did you mean 'http://...'?[/yellow]")
    config_manager.save_base_url(url)
    console.print(f"[green]API URL set to {url}[/green]")
