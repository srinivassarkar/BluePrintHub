"""Interactive CLI wizard for creating new project templates."""

import json
import shutil
from pathlib import Path

import questionary

from .core import TEMPLATES_DIR, save_template_metadata, console
from .templates import create_project


def _ask_question(prompt, qtype, **kwargs):
    """Wrapper for questionary calls to aid mocking."""
    if qtype == "select":
        return questionary.select(prompt, **kwargs).ask()
    if qtype == "checkbox":
        return questionary.checkbox(prompt, **kwargs).ask()
    if qtype == "text":
        return questionary.text(prompt, **kwargs).ask()
    if qtype == "confirm":
        return questionary.confirm(prompt, **kwargs).ask()
    return None


def run_create_wizard(dry_run: bool = False) -> None:
    """Run the interactive project creation wizard."""
    project_type = _ask_question(
        "Select project type:",
        "select",
        choices=[
            "Python CLI Tool",
            "FastAPI App",
            "Data Science Notebook",
            "Flask/Django REST API",
        ],
    )

    tech_stack = _ask_question(
        "Select tech stack:", "select", choices=["Basic", "Advanced"]
    )

    dep_manager = _ask_question(
        "Choose dependency manager:", "select", choices=["pip", "poetry", "uv"]
    )

    components = _ask_question(
        "Select optional components:",
        "checkbox",
        choices=["Docker", "CI/CD (GitHub Actions)", "Tests (pytest)", "pre-commit"],
    )

    project_name = _ask_question("Enter project directory name:", "text")
    output_dir = Path.cwd() / project_name

    import_repo = _ask_question("Import from a GitHub repo?", "confirm")
    if import_repo:
        from .github import import_github_repo

        github_url = _ask_question("Enter GitHub URL:", "text")
        import_github_repo(github_url)
        template_name = _ask_question(
            "Enter template name to save this config:", "text"
        )
        return

    template_map = {
        "Python CLI Tool": "python_cli",
        "FastAPI App": "fastapi_app",
        "Data Science Notebook": "data_science",
        "Flask/Django REST API": "flask_api",
    }
    template_name = template_map[project_type]

    metadata = {
        "name": _ask_question("Project name:", "text"),
        "author": _ask_question("Author:", "text"),
        "license": _ask_question(
            "License:", "select", choices=["MIT", "Apache 2.0", "GPLv3"]
        ),
        "version": _ask_question("Version:", "text", default="0.1.0"),
    }

    variables = metadata.copy()
    variables["dep_manager"] = dep_manager
    variables["components"] = components
    variables["tech_stack"] = tech_stack  # Now used to avoid 'unused-variable'

    create_project(template_name, output_dir, variables, dry_run=dry_run)

    if not dry_run:
        save_template = _ask_question(
            "Save this config as a reusable template?", "confirm"
        )
        if save_template:
            new_template_name = _ask_question("Enter template name:", "text")
            template_path = TEMPLATES_DIR / new_template_name
            shutil.copytree(output_dir, template_path, dirs_exist_ok=True)
            save_template_metadata(template_path, {"variables": variables, **metadata})
            console.print(f"Template saved as '{new_template_name}'.", style="green")

            config = {
                "template_name": new_template_name,
                "variables": variables,
                **metadata,
            }
            config_path = Path.cwd() / ".blueprint.json"
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(config, config_file, indent=2)
            console.print(f"Config saved to {config_path}", style="green")

        console.print(
            "Next steps: cd into your project and start coding!", style="bold green"
        )
