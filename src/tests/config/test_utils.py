from pathlib import Path

import pytest
from aim import Repo
from pytest_lazyfixture import lazy_fixture

from kedro_aim.config.model import RepositoryOptions
from kedro_aim.config.utils import load_repository


@pytest.fixture
def default_repo_option() -> RepositoryOptions:
    """Create a default repository options object.

    Returns:
        The default repository options object.
    """
    return RepositoryOptions()


@pytest.fixture
def initilized_repo_option(tmp_path: Path) -> RepositoryOptions:
    """Create a repository options object with a repository initialized.

    Returns:
        The repository options object.
    """
    return RepositoryOptions(path=str(tmp_path), init=True)


@pytest.mark.parametrize(
    "cfg",
    [
        lazy_fixture("default_repo_option"),
        lazy_fixture("initilized_repo_option"),
    ],
)
def test_repository_options(cfg: RepositoryOptions) -> None:
    """Test that repository options are loaded correctly."""
    repo = load_repository(cfg)

    if cfg.path is None:
        assert repo is None
    else:
        assert isinstance(repo, Repo)
        assert (Path(cfg.path) / ".aim").exists(), "The repository should be initilized"
