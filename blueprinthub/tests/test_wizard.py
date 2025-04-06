import pytest
from blueprinthub.wizard import run_create_wizard
from unittest.mock import patch


def test_wizard_dry_run():
    with patch(
        "blueprinthub.wizard._ask_question",
        side_effect=[
            "Python CLI Tool",  # project_type
            "Basic",  # tech_stack
            "poetry",  # dep_manager
            [],  # components
            "testproj",  # project_name (directory)
            False,  # import_repo
            "testcli",  # metadata: name
            "Test",  # metadata: author
            "MIT",  # metadata: license
            "0.1.0",  # metadata: version
            False,  # save_template
        ],
    ):
        run_create_wizard(dry_run=True)
