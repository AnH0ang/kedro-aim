from typing import List, Optional

from aim.ext.resource import DEFAULT_SYSTEM_TRACKING_INT
from pydantic import BaseModel, Extra, Field


class UiOptions(BaseModel):
    """Options for the ui command."""

    class Config:
        extra = Extra.forbid

    port: int = Field(default=43800, description="Port to run the aim UI on.")
    host: str = Field(default="127.0.0.1", description="Host to run the aim UI on.")


class RunOptions(BaseModel):
    """Options for the run command."""

    class Config:
        extra = Extra.forbid

    run_hash: Optional[str] = Field(
        default=None,
        description=(
            "The hash of the run. If a run hash is selected that already "
            "exists, it will be logged to that run."
        ),
    )
    experiment: Optional[str] = Field(
        default=None,
        description=(
            "The name of the experiment. 'default’ if not specified. "
            "Can be used later to query runs/sequences"
        ),
    )
    system_tracking_interval: Optional[int] = Field(
        default=DEFAULT_SYSTEM_TRACKING_INT,
        description=(
            "Sets the tracking interval in seconds for system usage metrics "
            "(CPU, Memory, etc.). Set to None to disable system metrics tracking."
        ),
    )
    log_system_params: Optional[bool] = Field(
        default=False,
        description=(
            "Enable/Disable logging of system params such as installed packages, "
            "git info, environment variables, etc."
        ),
    )
    capture_terminal_logs: Optional[bool] = Field(
        default=True, description="Enable/Disable the capturing of terminal logs."
    )
    tags: List[str] = Field(
        default_factory=list, description="List of tags for the run."
    )


class RepositoryOptions(BaseModel):
    """Options for the repository."""

    class Config:
        extra = Extra.forbid

    path: Optional[str] = Field(
        default=None, description="Path to the repository folder."
    )
    read_only: Optional[bool] = Field(
        default=None, description="Enable/Disable writes to repository."
    )
    init: bool = Field(
        default=False,
        description="Enable/Disable initialilzation of repository folder before run.",
    )


class DisableOptions(BaseModel):
    """Options for the disable command."""

    pipelines: List[str] = Field(
        default_factory=list,
        description="List of pipelines in which tracking with aim will be disabled.",
    )


class KedroAimConfig(BaseModel):
    """The pydantic model for the `aim.yml` file which configures this plugin."""

    class Config:
        extra = Extra.forbid

    ui: UiOptions = Field(UiOptions(), description="Options for the aim ui.")
    run: RunOptions = Field(RunOptions(), description="Options for the aim run.")
    repository: RepositoryOptions = Field(
        RepositoryOptions(), description="Configurations for the aim repository."
    )
    disable: DisableOptions = Field(
        DisableOptions(), description="Options for disabling aim tracking."
    )
