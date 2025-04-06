from typing import Optional
import typer
import questionary
import yaml
from pathlib import Path

from blueprinthub.templates import create_project, get_template_descriptions
from blueprinthub.github import import_github_repo

app = typer.Typer(
    help="BlueprintHub - Scalable CLI for project scaffolding and GitHub imports"
)


@app.command()
def list():
    """List all available templates and optionally select one to create."""
    templates = get_template_descriptions()
    if not templates:
        typer.echo("No templates available.")
        return

    typer.echo("Available templates:")
    for i, (name, desc) in enumerate(templates.items(), 1):
        typer.echo(f"{i}. {name}: {desc}")

    if questionary.confirm(
        "Would you like to create a project from one of these?"
    ).ask():
        template_name = questionary.select(
            "Select a template:", choices=[*templates.keys()]
        ).ask()
        if template_name:
            run_create(template_name)  # ✅ This avoids typer.ArgumentInfo issue


def run_create(template_name: str):
    """Helper function to create a project interactively (not CLI-exposed)."""
    templates = get_template_descriptions()
    if template_name not in templates:
        typer.echo(f"Template '{template_name}' not found.")
        raise typer.Exit(1)

    default_project_name = template_name
    variables = {
        "name": questionary.text("Project name", default=default_project_name).ask(),
        "author": questionary.text("Author name", default="Your Name").ask(),
        "version": "0.1.0",  # Added version variable to fix template rendering
        "dep_manager": questionary.select(
            "Package manager", choices=["poetry", "pip", "uv"], default="poetry"
        ).ask(),
        "components": [],
    }

    if "fastapi" in template_name or "flask" in template_name:
        variables["database"] = questionary.select(
            "Database",
            choices=["None", "SQLite", "PostgreSQL", "MySQL"],
            default="None",
        ).ask()
        if questionary.confirm("Include ORM?").ask():
            variables["orm"] = questionary.select(
                "ORM library",
                choices=["SQLAlchemy", "Tortoise ORM"],
                default="SQLAlchemy",
            ).ask()
    elif "data_science" in template_name:
        variables["libraries"] = questionary.checkbox(
            "Select libraries",
            choices=["numpy", "pandas", "matplotlib", "scikit-learn"],
        ).ask()
    elif "cli" in template_name:
        variables["cli_tool"] = questionary.select(
            "CLI framework", choices=["typer", "click"], default="typer"
        ).ask()

    if questionary.confirm("Include Docker?").ask():
        variables["components"].append("Docker")
    if questionary.confirm("Include CI/CD (GitHub Actions)?").ask():
        variables["components"].append("CI/CD (GitHub Actions)")
    extra_libs = questionary.text(
        "Additional libraries (comma-separated, e.g., pydantic, httpx)"
    ).ask()
    if extra_libs:
        variables["extra_libs"] = [lib.strip() for lib in extra_libs.split(",")]

    summary = yaml.dump(variables, default_flow_style=False)
    typer.echo("\nYour project configuration:")
    typer.echo(summary)

    if not questionary.confirm("Proceed with this configuration?").ask():
        typer.echo("Aborted.")
        return

    output_dir = variables["name"]
    typer.echo("✓ Creating project structure...")
    create_project(
        template_name, output_dir=Path(output_dir), variables=variables, dry_run=False
    )
    typer.echo(f"✓ Setting up dependencies with {variables['dep_manager']}...")
    typer.echo(f"✓ Project created successfully at ./{output_dir}")
    typer.echo("Next steps: cd into your project and start coding!")


@app.command()
def create(
    template_name: str = typer.Argument(..., help="Name of the template to use"),
    project_dir: Optional[str] = typer.Argument(None, help="Output directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview without creating files"
    ),
):
    """Create a project from a template with interactive options via CLI."""
    templates = get_template_descriptions()
    if template_name not in templates:
        typer.echo(f"Template '{template_name}' not found.")
        raise typer.Exit(1)

    default_project_name = project_dir if project_dir else template_name
    variables = {
        "name": questionary.text("Project name", default=default_project_name).ask(),
        "author": questionary.text("Author name", default="Your Name").ask(),
        "version": "0.1.0",  # Added version variable to fix template rendering
        "dep_manager": questionary.select(
            "Package manager", choices=["poetry", "pip", "uv"], default="poetry"
        ).ask(),
        "components": [],
    }

    if "fastapi" in template_name or "flask" in template_name:
        variables["database"] = questionary.select(
            "Database",
            choices=["None", "SQLite", "PostgreSQL", "MySQL"],
            default="None",
        ).ask()
        if questionary.confirm("Include ORM?").ask():
            variables["orm"] = questionary.select(
                "ORM library",
                choices=["SQLAlchemy", "Tortoise ORM"],
                default="SQLAlchemy",
            ).ask()
    elif "data_science" in template_name:
        variables["libraries"] = questionary.checkbox(
            "Select libraries",
            choices=["numpy", "pandas", "matplotlib", "scikit-learn"],
        ).ask()
    elif "cli" in template_name:
        variables["cli_tool"] = questionary.select(
            "CLI framework", choices=["typer", "click"], default="typer"
        ).ask()

    if questionary.confirm("Include Docker?").ask():
        variables["components"].append("Docker")
    if questionary.confirm("Include CI/CD (GitHub Actions)?").ask():
        variables["components"].append("CI/CD (GitHub Actions)")
    extra_libs = questionary.text(
        "Additional libraries (comma-separated, e.g., pydantic, httpx)"
    ).ask()
    if extra_libs:
        variables["extra_libs"] = [lib.strip() for lib in extra_libs.split(",")]

    summary = yaml.dump(variables, default_flow_style=False)
    typer.echo("\nYour project configuration:")
    typer.echo(summary)
    if not questionary.confirm("Proceed with this configuration?").ask():
        typer.echo("Aborted.")
        return

    output_dir = project_dir or variables["name"]
    if dry_run:
        typer.echo(
            f"[Dry Run] Would create '{output_dir}' from '{template_name}' with options: {variables}"
        )
        return

    typer.echo("✓ Creating project structure...")
    create_project(
        template_name, output_dir=Path(output_dir), variables=variables, dry_run=False
    )
    typer.echo(f"✓ Setting up dependencies with {variables['dep_manager']}...")
    typer.echo(f"✓ Project created successfully at ./{output_dir}")
    typer.echo("Next steps: cd into your project and start coding!")


@app.command(name="import")
def import_github(github_url: str):
    """Import a GitHub repository as a reusable template."""
    import_github_repo(github_url)


if __name__ == "__main__":
    app()
