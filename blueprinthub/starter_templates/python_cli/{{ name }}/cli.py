#!/usr/bin/env python3
"""
{{ name }} - Command Line Interface

A CLI tool with logging, configuration management and sample commands.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
{% if cli_tool == "click" %}
import click
{% elif cli_tool == "argparse" %}
import argparse
{% elif cli_tool == "typer" %}
import typer
from typing import Optional
{% endif %}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("{{ name }}")

# Configuration handling
def load_config(config_path=None):
    """Load configuration from YAML file"""
    if not config_path:
        # Look for config in standard locations
        config_locations = [
            Path.cwd() / "{{ name }}_config.yml",
            Path.home() / ".{{ name }}" / "config.yml",
            Path("/etc/{{ name }}/config.yml")
        ]
        
        for loc in config_locations:
            if loc.exists():
                config_path = loc
                break
    
    if not config_path or not Path(config_path).exists():
        logger.warning(f"No config file found, using defaults")
        return {}
    
    logger.info(f"Loading config from {config_path}")
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

{% if cli_tool == "click" %}
@click.group()
@click.option('--config', '-c', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """{{ name }} - A command-line tool"""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = load_config(config)

@cli.command('status')
@click.pass_context
def status_command(ctx):
    """Check the status of the application"""
    logger.info("Checking status...")
    config = ctx.obj['CONFIG']
    click.echo("Status: OK")
    if config:
        click.echo(f"Configuration loaded with {len(config)} settings")

@cli.command('run')
@click.argument('task')
@click.option('--priority', type=int, default=1, help='Task priority (1-5)')
@click.pass_context
def run_command(ctx, task, priority):
    """Run a specific task"""
    logger.info(f"Running task: {task} with priority {priority}")
    click.echo(f"Task '{task}' completed successfully")

if __name__ == '__main__':
    cli(obj={})
{% elif cli_tool == "argparse" %}
def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description='{{ name }} - A command-line tool'
    )
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check the status of the application')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a specific task')
    run_parser.add_argument('task', help='Task to run')
    run_parser.add_argument('--priority', type=int, default=1, help='Task priority (1-5)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    config = load_config(args.config)
    
    if args.command == 'status':
        logger.info("Checking status...")
        print("Status: OK")
        if config:
            print(f"Configuration loaded with {len(config)} settings")
    elif args.command == 'run':
        logger.info(f"Running task: {args.task} with priority {args.priority}")
        print(f"Task '{args.task}' completed successfully")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
{% elif cli_tool == "typer" %}
app = typer.Typer(help="{{ name }} - A command-line tool")
state = {"config": {}}

@app.callback()
def main(
    config: Optional[str] = typer.Option(None, '--config', '-c', help='Path to config file'),
    verbose: bool = typer.Option(False, '--verbose', '-v', help='Enable verbose output')
):
    """Initialize the CLI application"""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    state["config"] = load_config(config)

@app.command()
def status():
    """Check the status of the application"""
    logger.info("Checking status...")
    config = state["config"]
    typer.echo("Status: OK")
    if config:
        typer.echo(f"Configuration loaded with {len(config)} settings")

@app.command()
def run(
    task: str = typer.Argument(..., help="Task to run"),
    priority: int = typer.Option(1, help="Task priority (1-5)")
):
    """Run a specific task"""
    logger.info(f"Running task: {task} with priority {priority}")
    typer.echo(f"Task '{task}' completed successfully")

if __name__ == "__main__":
    app()
{% endif %}