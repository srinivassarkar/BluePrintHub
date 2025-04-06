import pytest
from typer.testing import CliRunner
from blueprinthub.cli import app
from pathlib import Path

runner = CliRunner(mix_stderr=True)


def test_list_command():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Local Templates" in result.output
    assert "Starter Templates" in result.output


def test_create_command(tmp_path):
    output_dir = tmp_path / "testcli"
    result = runner.invoke(
        app, ["create", "python_cli"], env={"OUTPUT_DIR": str(output_dir)}
    )
    assert result.exit_code == 0
    assert "Project rendered to" in result.output
    assert (output_dir / "testcli" / "cli.py").exists()


def test_create_dry_run():
    result = runner.invoke(app, ["create", "python_cli", "--dry-run"])
    assert result.exit_code == 0
    assert "[Dry Run]" in result.output
    assert "Would render" in result.output
