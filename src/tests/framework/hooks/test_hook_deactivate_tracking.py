from pathlib import Path
from typing import Dict

import pytest
import yaml
from aim import Run
from aim.sdk.repo import Repo
from kedro.framework.project import _ProjectPipelines  # type: ignore
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import Pipeline, node
from pytest import MonkeyPatch
from pytest_mock import MockerFixture


@pytest.fixture
def mock_failing_pipeline(mocker: MockerFixture) -> None:
    """Mock the pipeline regestry to contain a failing pipeline."""

    def foo(run: Run) -> None:
        run["foo"] = "bar"

    def mocked_register_pipelines() -> Dict[str, Pipeline]:
        pipeline_disabled = Pipeline(
            [
                node(
                    func=foo,
                    inputs=["run"],
                    outputs=None,
                )
            ]
        )

        pipeline_enabled = Pipeline(
            [
                node(
                    func=foo,
                    inputs=["run"],
                    outputs=None,
                )
            ]
        )
        return {
            "__default__": pipeline_disabled + pipeline_enabled,
            "pipeline_enabled": pipeline_enabled,
            "pipeline_disabled": pipeline_disabled,
        }

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_failing_pipeline")
def test_deactivate_tracking_for_given_pipeline(
    monkeypatch: MonkeyPatch, kedro_project_with_aim_config: Path
) -> None:
    """Check that tracking is deactivated for a pipeline when specified in `aim.yml`."""
    # change dir
    monkeypatch.chdir(kedro_project_with_aim_config)

    # overwrite aim config
    with open("./conf/local/aim.yml", "r") as f:
        cfg_dict = yaml.safe_load(f)
        cfg_dict["disable"]["pipelines"] = ["pipeline_disabled"]

    with open("./conf/local/aim.yml", "w") as f:
        yaml.dump(cfg_dict, f)

    # set up project
    bootstrap_project(kedro_project_with_aim_config)
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        # context = session.load_context()
        with pytest.raises(ValueError):
            session.run(pipeline_name="pipeline_disabled")

    # check that the repo is not initialized
    assert not (kedro_project_with_aim_config / ".aim").exists()


@pytest.mark.usefixtures("mock_failing_pipeline")
def test_deactivate_tracking_but_not_for_given_pipeline(
    monkeypatch: MonkeyPatch, kedro_project_with_aim_config: Path
) -> None:
    """Check that tracking is activated for a when not specified in `aim.yml`."""
    # change dir
    monkeypatch.chdir(kedro_project_with_aim_config)

    # overwrite aim config
    with open("./conf/local/aim.yml", "r") as f:
        cfg_dict = yaml.safe_load(f)
        cfg_dict["disable"]["pipelines"] = ["pipeline_disabled"]

    with open("./conf/local/aim.yml", "w") as f:
        yaml.dump(cfg_dict, f)

    # set up project
    bootstrap_project(kedro_project_with_aim_config)
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        # context = session.load_context()
        session.run(pipeline_name="pipeline_enabled")

    # check that the repo is initialized
    repo = Repo(str(kedro_project_with_aim_config))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"

    # check that the run is marked as failed
    run = runs[0]
    assert run["foo"] == "bar", "The run should have stored the foo key"
