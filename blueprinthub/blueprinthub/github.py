"""GitHub repository import functionality for BlueprintHub."""

from pathlib import Path
import tempfile
import shutil
from git import Repo
import questionary
import typer
from .core import TEMPLATES_DIR, render_template, save_template_metadata, console
from .utils import handle_error


def import_github_repo(github_url: str) -> None:
    """Import a GitHub repository as a template."""
    if (
        not github_url.startswith(("http://", "https://"))
        or "github.com" not in github_url
    ):
        console.print(
            "Error: Invalid GitHub URL. Must be a valid GitHub repository URL.",
            style="red",
        )
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        console.print(f"Cloning {github_url}...", style="yellow")
        try:
            Repo.clone_from(github_url, tmp_path, env={"GIT_ASKPASS": "false"})
        except Exception as e:
            handle_error(e, "Failed to clone repository")

        files = [
            str(f.relative_to(tmp_path))
            for f in tmp_path.rglob("*")
            if f.is_file() and ".git" not in str(f)
        ]
        if not files:
            console.print("No files found in repository.", style="red")
            raise typer.Exit(1)

        selected_files = questionary.checkbox(
            "Select files/folders to include in the template:", choices=files
        ).ask()
        if not selected_files:
            console.print("No files selected. Aborting.", style="red")
            raise typer.Exit(1)

        content_preview = {
            file: open(tmp_path / file, "r", encoding="utf-8").read()[:200]
            for file in selected_files[:3]
        }
        console.print("Preview of selected files:", content_preview)

        variables_input = questionary.text(
            "Enter strings to templatize (comma-separated):"
        ).ask()
        variables = (
            [v.strip() for v in variables_input.split(",")] if variables_input else []
        )

        # Map variables to standard keys
        standard_vars = ["name", "author", "version"]
        variable_map = {}
        for var in variables:
            if var:
                mapped_var = questionary.select(
                    f"Map '{var}' to which variable?",
                    choices=standard_vars + ["custom (enter manually)"],
                    default="name"
                    if "to-do" in var or "app" in var
                    else "author"
                    if "seenu" in var
                    else "version"
                    if "." in var
                    else "custom",
                ).ask()
                if mapped_var == "custom (enter manually)":
                    mapped_var = (
                        questionary.text(
                            f"Enter custom variable name for '{var}':"
                        ).ask()
                        or var
                    )
                variable_map[var] = mapped_var

        template_name = questionary.text("Enter a name for this template:").ask()
        if not template_name or not template_name.strip():
            console.print("Error: Template name cannot be empty.", style="red")
            raise typer.Exit(1)

        template_path = TEMPLATES_DIR / template_name
        try:
            template_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            console.print(
                f"Error: No permission to write to {TEMPLATES_DIR}.", style="red"
            )
            raise typer.Exit(1)

        name_dir = template_path / "{{ name }}"
        name_dir.mkdir(exist_ok=True)

        for file in selected_files:
            src = tmp_path / file
            dest = name_dir / Path(file).name
            try:
                with open(src, "r", encoding="utf-8") as src_file:
                    content = src_file.read()
                for orig_var, mapped_var in variable_map.items():
                    content = content.replace(orig_var, f"{{{{ {mapped_var} }}}}")
                with open(dest, "w", encoding="utf-8") as dest_file:
                    dest_file.write(content)
            except (IOError, UnicodeDecodeError) as e:
                handle_error(e, f"Failed to process file {file}")

        metadata = {
            "author": questionary.text("Author name:").ask() or "Unknown",
            "description": questionary.text("Template description:").ask()
            or "No description",
            "variables": variable_map,
            "main_file": "index.html",  # Default for React, adjust if needed
        }
        save_template_metadata(template_path, metadata)
        console.print(
            f"Template '{template_name}' imported successfully.", style="green"
        )
