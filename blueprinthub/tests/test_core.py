import pytest
from blueprinthub.core import render_template, TEMPLATES_DIR
from pathlib import Path


def test_render_template(tmp_path):
    # Use a starter template for testing
    template_path = Path(__file__).parent.parent / "starter_templates" / "python_cli"
    output_dir = tmp_path / "testcli"
    variables = {
        "name": "testcli",
        "author": "Test",
        "version": "0.1.0",
        "dep_manager": "poetry",
        "components": [],
    }
    render_template(template_path, output_dir, variables)
    assert (output_dir / "testcli" / "cli.py").exists()
    assert (output_dir / "pyproject.toml").exists()
