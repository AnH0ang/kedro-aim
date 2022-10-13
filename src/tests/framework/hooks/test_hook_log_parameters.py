from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd
import pytest
from aim import Repo
from kedro.framework.hooks import hook_impl
from kedro.framework.project import Validator  # type: ignore
from kedro.framework.project import _ProjectPipelines, _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from pytest import MonkeyPatch
from pytest_mock import MockerFixture


class DummyProjectHooks:  # pragma: no cover
    """A dummy project hooks class to replace kedro hooks."""

    @hook_impl
    def after_catalog_created(
        self,
        catalog: DataCatalog,
        conf_catalog: Dict[str, Any],
        conf_creds: Dict[str, Any],
        feed_dict: Dict[str, Any],
        save_version: str,
        load_versions: str,
    ) -> None:
        """Create a dummy data catalog with custom data sets.

        Args:
            catalog: Catalog to be updated.
            conf_catalog: Catalog configuration.
            conf_creds: Credentials configuration.
            feed_dict: Feed dictionary.
            save_version: Save version.
            load_versions: Load versions.
        """
        # HACK: Replace all AimArtifactDataSet with a AimArtifactDataSetChild dataset.
        # This is needed to pass a reference of the run to the dataset.
        catalog._data_sets.update(
            {
                "raw_data": MemoryDataSet(pd.DataFrame(data=[1], columns=["a"])),
                "params:unused_param": MemoryDataSet("blah"),
                "parameters": MemoryDataSet({"foo": "bar"}),
                "data": MemoryDataSet(),
            }
        )


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
        "kedro.framework.context.context.settings",
        "kedro.framework.session.session.settings",
        "kedro.framework.project.settings",
    ]:
        mocker.patch(path, mock_settings)
    return mock_settings


def _mock_settings_with_hooks(
    mocker: MockerFixture, hooks: Iterable[Any]
) -> _ProjectSettings:
    """Mock the settings with hooks.

    Args:
        mocker: A pytest-mock fixture.
        hooks: The hooks that are used instead.

    Returns:
        Mocked settings.
    """

    class MockSettings(_ProjectSettings):
        _HOOKS = Validator("HOOKS", default=hooks)

    return _mock_imported_settings_paths(mocker, MockSettings())


@pytest.fixture
def mock_settings_with_mlflow_hooks(mocker: MockerFixture) -> _ProjectSettings:
    """A fixture that mocks the settings with the mlflow hooks.

    Args:
        mocker: A pytest-mock fixture.

    Returns:
        THe mocked settings.
    """
    return _mock_settings_with_hooks(
        mocker,
        hooks=(DummyProjectHooks(),),
    )


@pytest.fixture
def mock_failing_pipeline(mocker: MockerFixture) -> None:
    """Mock the pipeline regestry to contain a failing pipeline.

    Args:
        mocker: A pytest-mock fixture.
    """

    def log_params(data: Any, params: str) -> None:
        ...

    def log_all_parameters(data: Any, parameters: Dict[str, Any]) -> None:
        ...

    def mocked_register_pipelines() -> Dict[str, Pipeline]:
        failing_pipeline = Pipeline(
            [
                node(
                    func=log_params,
                    inputs=["raw_data", "params:unused_param"],
                    outputs=None,
                ),
                node(
                    func=log_all_parameters,
                    inputs=["raw_data", "parameters"],
                    outputs=None,
                ),
            ]
        )
        return {"__default__": failing_pipeline, "pipeline_off": failing_pipeline}

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_settings_with_mlflow_hooks")
@pytest.mark.usefixtures("mock_failing_pipeline")
def test_parameter_logging(
    monkeypatch: MonkeyPatch, kedro_project_with_aim_config: Path
) -> None:
    """Check that the pipeline parameters are logged correctly."""
    # change directory to the project
    monkeypatch.chdir(kedro_project_with_aim_config)

    # initialize the project
    bootstrap_project(kedro_project_with_aim_config)

    # create a session
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        session.run()

    # check that the repo is initialized
    repo = Repo(str(kedro_project_with_aim_config))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"
    logging_run = runs[0]

    # check that the parameter is logged correctly
    assert logging_run["unused_param"] == "blah"

    # check that whole parameter config logged correctly
    assert logging_run["parameters"] == {"foo": "bar"}
