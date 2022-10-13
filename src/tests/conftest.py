from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.starters import TEMPLATE_PATH

from kedro_aim.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_aim.framework.cli.cli_utils import write_jinja_template

_FAKE_PYTHON_PACKAGE = "fake_project"
_FAKE_REPO_NAME = "fake-project"
_KEDRO_VERSION = kedro_version


@pytest.fixture
def kedro_project(tmp_path: Path) -> Path:
    """Create a Kedro project with the Kedro starter project.

    Args:
        tmp_path: A temporary path.

    Returns:
        The path to the Kedro project.
    """
    # TODO : this is also an integration test since this depends from the kedro version
    config = {
        "output_dir": tmp_path,
        "kedro_version": _KEDRO_VERSION,
        "project_name": "This is a fake project",
        "repo_name": _FAKE_REPO_NAME,
        "python_package": _FAKE_PYTHON_PACKAGE,
        "include_example": True,
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )

    return tmp_path / _FAKE_REPO_NAME


@pytest.fixture
def kedro_project_with_aim_config(kedro_project: Path) -> Path:
    """Create a Kedro project with the Kedro starter project with a `aim.yml` file.

    Args:
        kedro_project: A starter Kedro project.

    Returns:
        The path to the Kedro project.
    """
    write_jinja_template(
        src=TEMPLATE_FOLDER_PATH / "aim.yml",
        is_cookiecutter=False,
        dst=kedro_project / "conf" / "local" / "aim.yml",
        python_package="fake_project",
    )

    return kedro_project
