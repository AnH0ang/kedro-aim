import shutil
from pathlib import Path
from typing import Dict

import pytest
from aim import Text
from aim.sdk.repo import Repo
from kedro.framework.project import _ProjectPipelines  # type: ignore
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import Pipeline, node
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from kedro_aim.aim.utils import list_metrics_in_run


@pytest.fixture
def mock_failing_pipeline(mocker: MockerFixture) -> None:
    """Mock the pipeline regestry to contain a failing pipeline."""

    def artifact_generator() -> str:
        return "A funny joke."

    def mocked_register_pipelines() -> Dict[str, Pipeline]:
        artifact_pipeline = Pipeline(
            [
                node(
                    func=artifact_generator,
                    inputs=None,
                    outputs="text_artifact",
                )
            ]
        )
        return {"__default__": artifact_pipeline}

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_failing_pipeline")
def test_logging_of_artifact(
    monkeypatch: MonkeyPatch, kedro_project_with_aim_config: Path, datadir: Path
) -> None:
    """Check that artifacts are logged when written to the aim datsets."""
    # change dir
    monkeypatch.chdir(kedro_project_with_aim_config)

    # copy the catalog with the artifact configuration
    source_catalog = datadir / "catalog.yml"
    dest_catalog = kedro_project_with_aim_config / "conf" / "base" / "catalog.yml"
    shutil.copy(source_catalog, dest_catalog)

    # set up project
    bootstrap_project(kedro_project_with_aim_config)
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        # context = session.load_context()
        session.run()

    # check that the repo is initialized
    repo = Repo(str(kedro_project_with_aim_config))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"

    # check that the run is marked as failed
    run = runs[0]
    metrics = list(list_metrics_in_run(run))
    metric_names = [metric.name for metric in metrics]

    # check that the artifact is logged
    assert "funny_joke" in metric_names
    text_artifact = next(metric for metric in metrics if metric.name == "funny_joke")
    value_list = text_artifact.values.tolist()
    assert len(value_list) == 1
    text_value = value_list[0]
    assert isinstance(text_value, Text)
    assert text_value.data == "A funny joke."
