"""Core utilities for BlueprintHub."""

from pathlib import Path
from typing import Dict, Optional
import os
import jinja2
import questionary
import typer
import yaml
from rich.console import Console
import shutil

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
STARTER_TEMPLATES_DIR = Path(__file__).parent.parent / "starter_templates"
console = Console()


def load_template_metadata(template_path: Path) -> Dict[str, str]:
    """Load metadata from a .template.yml file if it exists."""
    metadata_file = template_path / ".template.yml"
    try:
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as file_handle:
                return yaml.safe_load(file_handle) or {}
    except (yaml.YAMLError, IOError) as e:
        console.print(f"Warning: Failed to load {metadata_file}: {e}", style="yellow")
    return {}


def save_template_metadata(template_path: Path, metadata: Dict[str, str]) -> None:
    """Save metadata to a .template.yml file."""
    metadata_file = template_path / ".template.yml"
    try:
        with open(metadata_file, "w", encoding="utf-8") as file_handle:
            yaml.safe_dump(metadata, file_handle)
    except IOError as e:
        console.print(f"Error: Failed to save {metadata_file}: {e}", style="red")
        raise typer.Exit(1)


def render_template(
    template_path: Path, output_dir: Path, variables: Dict[str, str]
) -> None:
    """Render a template directory with Jinja2, handling edge cases."""
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    if output_dir.exists():
        if not questionary.confirm(f"Directory {output_dir} exists. Overwrite?").ask():
            console.print("Aborted.", style="yellow")
            raise typer.Exit(0)
        try:
            shutil.rmtree(output_dir)
        except (OSError, PermissionError) as e:
            console.print(f"Error: Failed to clear {output_dir}: {e}", style="red")
            raise typer.Exit(1)

    if not template_path.exists():
        console.print(f"Error: Template path {template_path} not found.", style="red")
        raise typer.Exit(1)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path), undefined=jinja2.StrictUndefined
    )
    try:
        for root, _, files in os.walk(template_path):
            rel_root = Path(root).relative_to(template_path)
            output_root = (
                output_dir
                if str(rel_root) == "."
                else output_dir
                / rel_root.with_name(
                    variables.get("name", "unnamed")
                    if rel_root.name == "{{ name }}"
                    else rel_root.name
                )
            )
            output_root.mkdir(parents=True, exist_ok=True)
            for file in files:
                if file == ".template.yml":
                    continue
                try:
                    template = env.get_template(str(rel_root / file))
                    output_file = output_root / file
                    content = template.render(**variables)
                    with open(output_file, "w", encoding="utf-8") as file_handle:
                        file_handle.write(content)
                except jinja2.TemplateError as e:
                    console.print(f"Error rendering {file}: {e}", style="red")
                    raise typer.Exit(1)
    except (OSError, PermissionError) as e:
        console.print(f"Error creating files in {output_dir}: {e}", style="red")
        raise typer.Exit(1)


def generate_dependency_file(
    output_dir: Path, variables: Dict[str, str], metadata: Dict[str, str]
) -> None:
    """Generate dependency file based on dep_manager, with fallback."""
    dep_manager = variables.get("dep_manager", "poetry")
    extra_libs = variables.get("extra_libs", [])
    base_deps = metadata.get("dependencies", {}).get(dep_manager, [])
    extra_libs = [
        lib for lib in extra_libs if lib and lib.strip() and lib != "none"
    ]  # Filter junk

    try:
        if dep_manager == "poetry":
            deps = "\n".join(f'{lib} = "*"' for lib in base_deps + extra_libs)
            orm_dep = f'{variables["orm"]} = "*"' if variables.get("orm") else ""
            cli_dep = (
                f'{variables["cli_tool"]} = "*"' if variables.get("cli_tool") else ""
            )
            content = f"""[tool.poetry]
name = "{variables.get("name", "unnamed")}"
version = "{variables.get("version", "0.1.0")}"
description = ""
authors = ["{variables.get("author", "Unknown")}"]

[tool.poetry.dependencies]
python = "^3.10"
{deps}
{orm_dep}
{cli_dep}
"""
            with open(output_dir / "pyproject.toml", "w", encoding="utf-8") as f:
                f.write(content)
        elif dep_manager in ("pip", "uv"):
            extras = [variables.get("orm", ""), variables.get("cli_tool", "")]
            deps = [d for d in base_deps + extra_libs + extras if d]
            with open(output_dir / "requirements.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(deps))
        else:
            console.print(
                f"Warning: Unsupported dep_manager '{dep_manager}', skipping dependency file.",
                style="yellow",
            )
    except IOError as e:
        console.print(f"Error writing dependency file: {e}", style="red")
        raise typer.Exit(1)


def generate_component_files(
    output_dir: Path, variables: Dict[str, str], metadata: Dict[str, str]
) -> None:
    """Generate files for selected components, with fallback."""
    components = variables.get("components", [])
    dep_manager = variables.get("dep_manager", "poetry")
    main_file = metadata.get("main_file", "main.py")

    try:
        if "Docker" in components:
            cmd = f"{'poetry run python' if dep_manager == 'poetry' else 'python'} {variables.get('name', 'unnamed')}/{main_file}"
            docker_content = f"""FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN {"poetry install" if dep_manager == "poetry" else "pip install -r requirements.txt"}
CMD ["sh", "-c", "{cmd}"]
"""
            with open(output_dir / "Dockerfile", "w", encoding="utf-8") as f:
                f.write(docker_content)
        if "CI/CD (GitHub Actions)" in components:
            os.makedirs(output_dir / ".github/workflows", exist_ok=True)
            with open(
                output_dir / ".github/workflows/ci.yml", "w", encoding="utf-8"
            ) as f:
                f.write("""name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: poetry install
      - run: poetry run pytest
""")
    except (OSError, IOError) as e:
        console.print(f"Error generating component files: {e}", style="red")
        raise typer.Exit(1)
