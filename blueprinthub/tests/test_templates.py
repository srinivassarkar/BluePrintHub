import pytest
from typer.testing import CliRunner
from blueprinthub.cli import app
from pathlib import Path

runner = CliRunner()


def test_create_project_dry_run(tmp_path):
    result = runner.invoke(app, ["create", "fastapi_app", "--dry-run"])
    assert result.exit_code == 0
    assert "[Dry Run]" in result.output
    assert not (tmp_path / "fastapi_app").exists()


def test_create_invalid_template():
    result = runner.invoke(app, ["create", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output
