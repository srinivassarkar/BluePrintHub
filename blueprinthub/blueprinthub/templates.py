from pathlib import Path
from typing import Optional, Dict
import typer
from .core import (
    TEMPLATES_DIR,
    STARTER_TEMPLATES_DIR,
    render_template,
    load_template_metadata,
    generate_dependency_file,
    generate_component_files,
    console,
)


def get_template_descriptions() -> Dict[str, str]:
    """Return a dictionary of template names and their descriptions."""
    templates = {}
    for dir_path in (TEMPLATES_DIR, STARTER_TEMPLATES_DIR):
        for template_dir in dir_path.iterdir():
            if template_dir.is_dir():
                try:
                    metadata = load_template_metadata(template_dir) or {}
                    desc = metadata.get("description", "No description available")
                except FileNotFoundError:
                    desc = "No description available"
                templates[template_dir.name] = desc
    return templates


def create_project(
    template_name: str,
    output_dir: Optional[Path] = None,
    variables: Optional[dict] = None,
    dry_run: bool = False,
) -> None:
    """Create a project from a template."""
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        template_path = STARTER_TEMPLATES_DIR / template_name
        if not template_path.exists():
            console.print(f"Template '{template_name}' not found.", style="red")
            raise typer.Exit(1)

    metadata = load_template_metadata(template_path) or {}
    variables = variables or metadata.get("variables", {})
    output_dir = output_dir or Path.cwd() / template_name

    if dry_run:
        console.print(
            f"[Dry Run] Would render {template_path} to {output_dir} with variables: {variables}",
            style="yellow",
        )
        return

    render_template(template_path, output_dir, variables)
    generate_dependency_file(output_dir, variables, metadata)
    generate_component_files(output_dir, variables, metadata)
    console.print(f"Project rendered to {output_dir}", style="green")
