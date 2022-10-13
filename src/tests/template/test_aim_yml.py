from pathlib import Path

import pytest
import yaml

from kedro_aim.config import KedroAimConfig
from kedro_aim.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_aim.framework.cli.cli_utils import write_jinja_template


@pytest.fixture
def template_aimyml(tmp_path: Path) -> str:
    """Create a template aim.yml file.

    Returns:
        The path to the template aim.yml file.
    """
    # the goal is to discover all potential ".py" files
    # but for now there is only "run.py"
    # this is rather a safeguard for further add
    raw_template_path = TEMPLATE_FOLDER_PATH / "aim.yml"
    rendered_template_path = tmp_path / raw_template_path.name
    tags = {
        "project_name": "This is a fake project",
        "python_package": "fake_project",
        "kedro_version": "0.16.0",
    }

    write_jinja_template(src=raw_template_path, dst=rendered_template_path, **tags)
    return rendered_template_path.as_posix()


def test_aim_yml_rendering(template_aimyml: str) -> None:
    """Check that the `aim.yml` file is rendered correctly."""
    # check that the template is valid yaml and can be parsed
    with open(template_aimyml, "r") as file_handler:
        aim_config = yaml.safe_load(file_handler)
    KedroAimConfig.parse_obj(aim_config)
