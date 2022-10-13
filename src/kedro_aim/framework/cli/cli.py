import subprocess
from logging import getLogger
from pathlib import Path
from typing import Dict, List, Optional

import click
from click.core import Command, Context
from kedro.framework.project import settings
from kedro.framework.session import KedroSession
from kedro.framework.startup import _is_project, bootstrap_project

from kedro_aim.config import KedroAimConfig
from kedro_aim.framework.cli.cli_utils import write_jinja_template

LOGGER = getLogger(__name__)
TEMPLATE_FOLDER_PATH = Path(__file__).parent.parent.parent / "template" / "config"


class KedroClickGroup(click.Group):
    """The main entry point for the Kedro CLI."""

    def reset_commands(self) -> None:
        """Reset the commands to the default ones."""
        self.commands: Dict[str, Command] = {}

        # add commands on the fly based on conditions
        if _is_project(Path.cwd()):
            self.add_command(init)  # type: ignore
            self.add_command(ui)  # type: ignore

    def list_commands(self, ctx: Context) -> List[str]:
        """List the names of all commands.

        Args:
            ctx: The click context.

        Returns:
            A list of command names.
        """
        self.reset_commands()
        commands_list = sorted(self.commands)
        return commands_list

    def get_command(self, ctx: Context, cmd_name: str) -> Optional[click.Command]:
        """Get a click command by name.

        Args:
            ctx: The click context.
            cmd_name: The name of the command.

        Returns:
            The click command with the given name.
        """
        self.reset_commands()
        return self.commands.get(cmd_name)


@click.group(name="Aim")
def commands() -> None:
    """Kedro plugin for interactions with aim."""
    pass  # pragma: no cover


@commands.command(name="aim", cls=KedroClickGroup)
def aim_commands() -> None:
    """Use aim-specific commands inside kedro project."""
    pass  # pragma: no cover


@aim_commands.command()  # type: ignore
@click.option(
    "--env",
    "-e",
    default="local",
    help=(
        "The name of the kedro environment where the 'aim.yml' should be created. "
        "Default to 'local'"
    ),
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Update the template without any checks.",
)
@click.option(
    "--silent",
    "-s",
    is_flag=True,
    default=False,
    help="Should message be logged when files are modified?",
)
def init(env: str, force: bool, silent: bool) -> None:
    """Updates the template of a kedro project.

    Running this command is mandatory to use kedro-aim.
    This adds "conf/base/aim.yml": This is a configuration file
    used for run parametrization when calling "kedro run" command.
    """
    # get constants
    aim_yml = "aim.yml"
    project_path = Path().cwd()
    project_metadata = bootstrap_project(project_path)
    aim_yml_path: Path = (
        project_path / settings.CONF_SOURCE / env / aim_yml  # type: ignore
    )

    # aim.yml is just a static file,
    # but the name of the experiment is set to be the same as the project
    if aim_yml_path.is_file() and not force:
        click.secho(
            click.style(
                (
                    f"A 'aim.yml' already exists at '{aim_yml_path}'. "
                    "You can use the ``--force`` option to override it."
                ),
                fg="red",
            )
        )
    else:
        try:
            write_jinja_template(
                src=TEMPLATE_FOLDER_PATH / aim_yml,
                is_cookiecutter=False,
                dst=aim_yml_path,
                python_package=project_metadata.package_name,
            )
            if not silent:
                click.secho(
                    click.style(
                        (
                            f"'{settings.CONF_SOURCE}/{env}/{aim_yml}' "
                            "successfully updated."
                        ),
                        fg="green",
                    )
                )
        except FileNotFoundError:
            click.secho(
                click.style(
                    (
                        f"No env '{env}' found. "
                        "Please check this folder exists inside "
                        f"'{settings.CONF_SOURCE}' folder.",
                    ),
                    fg="red",
                )
            )


@aim_commands.command()  # type: ignore
@click.option(
    "--env",
    "-e",
    required=False,
    default="local",
    help="The environment within conf folder we want to retrieve.",
)
@click.option(
    "--port",
    "-p",
    required=False,
    type=int,
    help="The port to listen on",
)
@click.option(
    "--host",
    "-h",
    required=False,
    help=(
        "The network address to listen on (default: 127.0.0.1). "
        "Use 0.0.0.0 to bind to all addresses if you want to access the tracking "
        "server from other machines."
    ),
)
def ui(env: str, port: int, host: str) -> None:
    """Start the aim UI.

    Opens the aim user interface with the project-specific settings of aim.yml.
    This interface enables to browse and compares runs.
    """
    project_path = Path().cwd()
    bootstrap_project(project_path)
    with KedroSession.create(
        project_path=project_path,
        env=env,
    ) as session:

        context = session.load_context()
        aim_config: KedroAimConfig = context.aim  # type: ignore
        host = host or aim_config.ui.host
        port = port or aim_config.ui.port

        subprocess.call(
            [
                "aim",
                "up",
                "--port",
                str(port),
                "--host",
                host,
            ]
        )
