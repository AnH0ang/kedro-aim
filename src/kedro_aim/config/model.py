from typing import List, Optional

from aim.ext.resource import DEFAULT_SYSTEM_TRACKING_INT
from pydantic import BaseModel, Extra, Field


class UiOptions(BaseModel):
    """Options for the ui command."""

    class Config:
        extra = Extra.forbid

    port: int = 43800
    host: str = "127.0.0.1"


class RunOptions(BaseModel):
    """Options for the run command."""

    class Config:
        extra = Extra.forbid

    run_hash: Optional[str] = None
    experiment: Optional[str] = None
    system_tracking_interval: Optional[int] = DEFAULT_SYSTEM_TRACKING_INT
    log_system_params: Optional[bool] = False
    capture_terminal_logs: Optional[bool] = True
    tags: List[str] = Field(default_factory=list)


class RepositoryOptions(BaseModel):
    """Options for the repository."""

    class Config:
        extra = Extra.forbid

    path: Optional[str] = None
    read_only: Optional[bool] = None
    init: bool = False


class DisableOptions(BaseModel):
    """Options for the disable command."""

    pipelines: List[str] = Field(default_factory=list)


class KedroAimConfig(BaseModel):
    """The pydantic model for the `aim.yml` file which configures this plugin."""

    class Config:
        extra = Extra.forbid

    ui: UiOptions = UiOptions()
    run: RunOptions = RunOptions()
    repository: RepositoryOptions = RepositoryOptions()
    disable: DisableOptions = DisableOptions()
