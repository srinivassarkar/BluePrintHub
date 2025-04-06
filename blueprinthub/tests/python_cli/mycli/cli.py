from typing import Optional
import typer
from loguru import logger
import yaml
import sys
from pathlib import Path

app = typer.Typer()

CONFIG_PATH = Path.home() / ".mycli" / "config.yml"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {"greeting": "Hello"}


@app.command()
def greet(name: str, config: Optional[str] = typer.Option(None, "--config")):
    """Greet a user with a configurable message."""
    logger.add(sys.stderr, format="{time} - {level} - {message}", level="INFO")
    cfg = load_config()
    if config:
        with open(config, "r") as f:
            cfg.update(yaml.safe_load(f))
    logger.info(f"Greeted {name}")
    typer.echo(f"{cfg['greeting']}, {name}!")


if __name__ == "__main__":
    app()