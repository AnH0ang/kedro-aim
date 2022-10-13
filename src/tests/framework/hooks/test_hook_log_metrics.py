from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest
from aim import Figure, Repo, Run
from kedro import __version__ as kedro_version
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner
from matplotlib import pyplot as plt
from pytest import MonkeyPatch

from kedro_aim.aim.utils import list_metrics_in_run
from kedro_aim.framework.hooks import AimHook


@pytest.fixture
def dummy_pipeline() -> Pipeline:
    """Creates a dummy pipeline that logs various metrics to the aim run.

    Returns:
        A dummy pipeline.
    """

    def preprocess_fun(data: Any) -> Any:
        return data

    def log_metrics(run: Run, model: Any) -> None:
        run.track(value=1, name="score", context={"subset": "validation"})
        run.track(value=1, name="score", context={"subset": "test"})

    def log_params(run: Run, data: Any) -> Any:
        run["model"] = "model"
        return 2

    def log_figure(run: Run) -> None:
        fig = plt.figure()
        plt.plot([1, 2, 3])
        plt.close(fig)
        run.track(value=Figure(fig), name="mpl_figure")

    def predict_fun(model: Any, data: Any) -> Any:
        return data * model

    dummy_pipeline = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
            ),
            node(
                func=log_params,
                inputs=["run", "data"],
                outputs="model",
            ),
            node(
                func=log_metrics,
                inputs=["run", "model"],
                outputs=None,
            ),
            node(
                func=log_figure,
                inputs=["run"],
                outputs=None,
            ),
            node(
                func=predict_fun,
                inputs=["model", "data"],
                outputs="predictions",
            ),
        ]
    )
    return dummy_pipeline


@pytest.fixture
def dummy_catalog(tmp_path: Path) -> DataCatalog:
    """Creates dummy kedro data catalog.

    Returns:
        A dummy kedro data catalog.
    """
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(pd.DataFrame(data=[1], columns=["a"])),
            "params:unused_param": MemoryDataSet("blah"),
            "data": MemoryDataSet(),
            "model": PickleDataSet((tmp_path / "model.pkl").as_posix()),
        }
    )
    return dummy_catalog


@pytest.fixture
def dummy_run_params(tmp_path: Path) -> Dict[str, Any]:
    """Dummy kedro run parameters.

    Returns:
        Dummy kedro run parameters.
    """
    dummy_run_params = {
        "project_path": tmp_path.as_posix(),
        "env": "local",
        "kedro_version": kedro_version,
        "tags": [],
        "from_nodes": [],
        "to_nodes": [],
        "node_names": [],
        "from_inputs": [],
        "load_versions": [],
        "pipeline_name": "my_cool_pipeline",
        "extra_params": [],
    }
    return dummy_run_params


def test_aim_hook_logging_metrics(
    monkeypatch: MonkeyPatch,
    kedro_project_with_aim_config: Path,
    dummy_pipeline: Pipeline,
    dummy_run_params: Dict[str, Any],
    dummy_catalog: DataCatalog,
) -> None:
    """Check tha aim hook correctly logs metrics to the aim run."""
    # change directory to the project
    monkeypatch.chdir(kedro_project_with_aim_config)

    # initialize the project
    bootstrap_project(kedro_project_with_aim_config)

    # create a session
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        context = session.load_context()

        # create hook
        aim_hook = AimHook()

        runner = SequentialRunner()

        aim_hook.after_context_created(context)
        aim_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
        )
        aim_hook.before_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )
        runner.run(dummy_pipeline, dummy_catalog, hook_manager=None)  # type: ignore

        aim_hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )

    # check that the repo is initialized
    repo = Repo(str(kedro_project_with_aim_config))
    runs = list(repo.iter_runs())
    assert len(runs) == 1, "There should be only one run"
    logging_run = runs[0]

    # check that the run has stored the correct params
    assert logging_run["model"] == "model", "Model should be saved in the run"

    # get metrics from the run
    metrics = list(list_metrics_in_run(logging_run))

    # check that the run has stored the correct metrics
    score_metrics = [m for m in metrics if m.name == "score"]
    assert all(1 in m.values.values_numpy() for m in score_metrics)
    assert all("subset" in m.context for m in score_metrics)

    # check that the run has stored the correct figure
    figure_metric = next((m for m in metrics if m.name == "mpl_figure"), None)
    assert (
        figure_metric is not None
    ), "Figure should be saved in the run with key `mpl_figure`"
    figure_list = figure_metric.values.tolist()
    assert len(figure_list) == 1, "There should be only one figure in the run"
    assert isinstance(figure_list[0], Figure), "Figure should be of type `aim.Figure`"
