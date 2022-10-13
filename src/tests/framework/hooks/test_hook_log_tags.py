import shutil
from pathlib import Path
from typing import Dict

import pytest
from aim import Run
from aim.sdk.repo import Repo
from kedro.framework.project import _ProjectPipelines  # type: ignore
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import Pipeline, node
from pytest import MonkeyPatch
from pytest_mock import MockerFixture


@pytest.fixture
def mock_dummy_pipeline(mocker: MockerFixture) -> None:
    """Mock the pipeline regestry to contain a dummy pipeline."""

    def tag_run(run: Run) -> int:
        run.add_tag("run_tag")
        return 0

    def mocked_register_pipelines() -> Dict[str, Pipeline]:
        return {
            "__default__": Pipeline(
                [node(func=tag_run, inputs="run", outputs="output")]
            )
        }

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_dummy_pipeline")
def test_tagging_of_pipeline(
    monkeypatch: MonkeyPatch, kedro_project: Path, datadir: Path
) -> None:
    """Check that the run is tagged with the tags in `aim.yml`."""
    # change dir
    monkeypatch.chdir(kedro_project)

    # copy the catalog with the artifact configuration
    source_cfg = datadir / "aim.yml"
    destination_cfg = kedro_project / "conf" / "local" / "aim.yml"
    shutil.copy(source_cfg, destination_cfg)

    # set up project
    bootstrap_project(kedro_project)
    with KedroSession.create(project_path=kedro_project) as session:
        # context = session.load_context()
        session.run()

    # check that the repo is initialized
    repo = Repo(str(kedro_project))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"

    # check that the run is marked as failed
    run = runs[0]
    assert "cfg_tag" in set(run.tags), "The run should contain the tags from `aim.yml`."
    assert "run_tag" in set(
        run.tags
    ), "The run should contain the tags from the pipeline."
