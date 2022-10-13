from pathlib import Path
from typing import Dict

import pytest
from aim.sdk.repo import Repo
from kedro.framework.project import _ProjectPipelines  # type: ignore
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import Pipeline, node
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from kedro_aim.framework.hooks.aim_hook import StatusTag


@pytest.fixture
def mock_failing_pipeline(mocker: MockerFixture) -> None:
    """Mock the pipeline regestry to contain a failing pipeline."""

    def failing_node() -> None:
        raise ValueError("Let's make this pipeline fail")

    def mocked_register_pipelines() -> Dict[str, Pipeline]:
        failing_pipeline = Pipeline(
            [
                node(
                    func=failing_node,
                    inputs=None,
                    outputs="fake_output",
                )
            ]
        )
        return {"__default__": failing_pipeline, "pipeline_off": failing_pipeline}

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_failing_pipeline")
def test_on_pipeline_error(
    monkeypatch: MonkeyPatch, kedro_project_with_aim_config: Path
) -> None:
    """Check that a failing pipeline is tagged as failed."""
    # change dir
    monkeypatch.chdir(kedro_project_with_aim_config)

    # set up project
    bootstrap_project(kedro_project_with_aim_config)
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        # context = session.load_context()
        with pytest.raises(ValueError):
            session.run()

    # check that the repo is initialized
    repo = Repo(str(kedro_project_with_aim_config))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"

    # check that the run is marked as failed
    run = runs[0]
    assert StatusTag.FAILURE in run.tags, "The run should be tagged as 'failure'"
