import re
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest
import yaml
from click.testing import CliRunner
from kedro.framework.cli.cli import info
from kedro.framework.project import _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from kedro_aim.config import KedroAimConfig
from kedro_aim.framework.cli.cli import aim_commands as cli_aim
from kedro_aim.framework.cli.cli import init as cli_init
from kedro_aim.framework.cli.cli import ui as cli_ui


def extract_cmd_from_help(msg: str) -> List[str]:
    """Extract the commands from the help message.

    Args:
        msg: The help message.

    Returns:
        The list of commands.
    """
    # [\s\S] is used instead of "." to match any character including new lines
    cmd_txt = re.search((r"(?<=Commands:)([\s\S]+)$"), msg).group(1)  # type: ignore
    cmd_list_detailed = cmd_txt.split("\n")

    cmd_list = []
    for cmd_detailed in cmd_list_detailed:
        cmd_match = re.search(r"\w+(?=  )", string=cmd_detailed)
        if cmd_match is not None:
            cmd_list.append(cmd_match.group(0))
    return cmd_list


@pytest.fixture(autouse=True)
def mock_validate_settings(mocker: MockerFixture) -> None:
    """Mock the validate_settings function."""
    # KedroSession eagerly validates that a project's settings.py is correct by
    # importing it. settings.py does not actually exists as part of this test suite
    # since we are testing session in isolation, so the validation is patched.
    mocker.patch("kedro.framework.session.session.validate_settings")


def _mock_imported_settings_paths(
    mocker: MockerFixture, mock_settings: _ProjectSettings
) -> _ProjectSettings:
    """Mock the imported settings paths from kedro.

    Args:
        mocker: A pytest-mock fixture.
        mock_settings: The settings that are used instead.

    Returns:
        The mocked settings.
    """
    for path in [
        "kedro.framework.project.settings",
        "kedro.framework.session.session.settings",
    ]:
        mocker.patch(path, mock_settings)
    return mock_settings


@pytest.fixture
def mock_settings_fake_project(mocker: MockerFixture) -> _ProjectSettings:
    """Mock the settings for a fake project.

    Returns:
        The mocked settings.
    """
    return _mock_imported_settings_paths(mocker, _ProjectSettings())


def test_cli_global_discovered(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Check that the global commands are discovered."""
    # Change the current working directory to the temporary directory
    monkeypatch.chdir(tmp_path)

    # Run the info command to trigger the discovery of the global CLI
    cli_runner = CliRunner()
    result = cli_runner.invoke(info)
    assert result.exit_code == 0

    # Check that the plugin is listed in the output
    plugin_line = next(
        (ln for ln in result.output.splitlines() if "kedro_aim" in ln), None
    )
    assert plugin_line is not None, "Plugin not found in the output of `kedro info`"

    # Check that the plugin hooks are listed in the output
    assert "hooks,project" in plugin_line, "Hooks are not correctly installed"


def test_aim_commands_inside_kedro_project(
    monkeypatch: MonkeyPatch, kedro_project: Path
) -> None:
    """Check that the aim commands are discovered when inside a kedro project."""
    # Change the current working directory to the kedro project
    monkeypatch.chdir(kedro_project)

    # launch the command to initialize the project
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_aim)
    assert {"init", "ui"} == set(extract_cmd_from_help(result.output))
    assert "You have not updated your template yet" not in result.output


def test_cli_init(monkeypatch: MonkeyPatch, kedro_project: Path) -> None:
    """Check that this `aim init` creates an `aim.yml` file."""
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init, catch_exceptions=False)  # type: ignore

    # FIRST TEST:
    # the command should have executed propery
    assert result.exit_code == 0

    # check aim.yml file
    assert "'conf/local/aim.yml' successfully updated." in result.output
    assert (kedro_project / "conf" / "local" / "aim.yml").is_file()


def test_cli_init_existing_config(
    monkeypatch: MonkeyPatch,
    kedro_project_with_aim_config: Path,
    mock_settings_fake_project: _ProjectSettings,
) -> None:
    """Check that `aim init` does not overwrite an existing `aim.yml` file."""
    # "kedro_project" is a pytest.fixture declared in conftest
    cli_runner = CliRunner()
    monkeypatch.chdir(kedro_project_with_aim_config)
    bootstrap_project(kedro_project_with_aim_config)

    with KedroSession.create(
        "fake_project", project_path=kedro_project_with_aim_config
    ) as session:
        # check that file already exists
        yaml_str = yaml.dump(dict(ui=dict(port="1234", host="test")))
        (
            kedro_project_with_aim_config
            / mock_settings_fake_project.CONF_SOURCE  # type: ignore
            / "local"
            / "aim.yml"
        ).write_text(yaml_str)
        result = cli_runner.invoke(cli_init)  # type: ignore

        # check an error message is raised
        assert "A 'aim.yml' already exists" in result.output

        context = session.load_context()
        aim_cfg: KedroAimConfig = context.aim  # type: ignore
        assert aim_cfg.ui.host == "test"


@pytest.mark.parametrize(
    "env",
    ["base", "local"],
)
def test_cli_init_with_env(
    monkeypatch: MonkeyPatch, kedro_project: Path, env: str
) -> None:
    """Check that `aim init` creates an `aim.yml` file in correct environment."""
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init, f"--env {env}")  # type: ignore

    # FIRST TEST:
    # the command should have executed propery
    assert result.exit_code == 0

    # check aim.yml file
    assert f"'conf/{env}/aim.yml' successfully updated." in result.output
    assert (kedro_project / "conf" / env / "aim.yml").is_file()


@pytest.mark.parametrize(
    "env",
    ["debug"],
)
def test_cli_init_with_wrong_env(
    monkeypatch: MonkeyPatch, kedro_project: Path, env: str
) -> None:
    """Check that the `aim init` fails when the environment is not valid."""
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init, f"--env {env}")  # type: ignore

    # A warning message should appear
    assert f"No env '{env}' found" in result.output


def test_ui_is_up(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, kedro_project_with_aim_config: Path
) -> None:
    """Check that the `aim ui` command launches the UI."""
    monkeypatch.chdir(kedro_project_with_aim_config)
    cli_runner = CliRunner()

    # This does not test anything : the goal is to check whether it raises an error
    ui_mocker = mocker.patch(
        "subprocess.call"
    )  # make the test succeed, but no a real test
    cli_runner.invoke(cli_ui)  # type: ignore
    ui_mocker.assert_called_once_with(
        [
            "aim",
            "up",
            "--port",
            "43800",
            "--host",
            "127.0.0.1",
        ]
    )


def test_aim_is_found(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, kedro_project_with_aim_config: Path
) -> None:
    """Check that the `aim` command is found by `kedro`."""
    monkeypatch.chdir(kedro_project_with_aim_config)
    r = subprocess.run([sys.executable, "-m", "kedro", "--help"], capture_output=True)
    assert "aim" in r.stdout.decode("utf-8")
