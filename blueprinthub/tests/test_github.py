import pytest
from typer.testing import CliRunner
from blueprinthub.cli import app

runner = CliRunner(mix_stderr=True)


def test_import_invalid_url():
    result = runner.invoke(app, ["import", "https://github.com/invalid/repo"])
    assert result.exit_code == 1  # handle_error raises typer.Exit(1)
    assert "Failed to clone repository" in result.output
