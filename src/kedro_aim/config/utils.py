from typing import Optional

from aim.sdk.repo import Repo

from kedro_aim.config.model import RepositoryOptions


def load_repository(cfg: RepositoryOptions) -> Optional[Repo]:
    """Load the a aim repository from the config options.

    Args:
        cfg: Config for the repository.

    Returns:
        A aim repository or None if the repository is disabled.
    """
    if cfg.path is None:
        return None
    else:
        return Repo(path=cfg.path, read_only=cfg.read_only, init=cfg.init)
