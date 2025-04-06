from rich.console import Console
import typer

console = Console()


def handle_error(e: Exception, message: str) -> None:
    """Gracefully handle and display errors."""
    console.print(f"{message}: {str(e)}", style="red")
    raise typer.Exit(1)
