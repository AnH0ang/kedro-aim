from pathlib import Path
from typing import Any, Dict, Generator, Tuple

import numpy as np
import pytest
from aim import Audio, Figure, Image, Text
from kedro import __version__ as kedro_version
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node
from matplotlib import pyplot as plt
from matplotlib.figure import Figure as MplFigure
from pytest import MonkeyPatch
from pytest_lazyfixture import lazy_fixture

from kedro_aim.aim.utils import list_metrics_in_run
from kedro_aim.framework.hooks import AimHook
from kedro_aim.io.artifacts import make_run_dataset
from kedro_aim.io.artifacts.aim_artifact_dataset import AimArtifactDataSet, ArtifactType


@pytest.fixture
def dummy_pipeline() -> Pipeline:
    """Create a dummy pipeline.

    Returns:
        A dummy pipeline.
    """

    def foo(x: int) -> int:
        return x

    dummy_pipeline = Pipeline([node(func=foo, inputs=["input"], outputs=["output"])])
    return dummy_pipeline


@pytest.fixture
def dummy_catalog() -> DataCatalog:
    """Create a dummy catalog.

    Returns:
        A dummy catalog.
    """
    dummy_catalog = DataCatalog({})
    return dummy_catalog


@pytest.fixture
def dummy_run_params(tmp_path: Path) -> Dict[str, Any]:
    """Create a dummy run parameters.

    Args:
        tmp_path: A temporary path.

    Returns:
        Dummy run parameters.
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


@pytest.fixture
def aim_hook_after_catalog_created(
    monkeypatch: MonkeyPatch,
    kedro_project_with_aim_config: Path,
    dummy_catalog: DataCatalog,
) -> Generator[AimHook, None, None]:
    """Create an AimHook in state right after the data catalog is created.

    Args:
        monkeypatch: A pytest monkeypatch fixture.
        kedro_project_with_aim_config: The path to a kedro project with an aim config.
        dummy_catalog: A dummy catalog.

    Yields:
        A AimHook object.
    """
    # change directory to the project
    monkeypatch.chdir(kedro_project_with_aim_config)

    # initialize the project
    bootstrap_project(kedro_project_with_aim_config)

    # create a session
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        context = session.load_context()

        # create hook
        hook = AimHook()

        hook.after_context_created(context)
        hook.after_catalog_created(
            catalog=dummy_catalog,
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
        )
        yield hook


@pytest.fixture
def aim_hook_during_run(
    monkeypatch: MonkeyPatch,
    kedro_project_with_aim_config: Path,
    dummy_pipeline: Pipeline,
    dummy_run_params: Dict[str, Any],
    dummy_catalog: DataCatalog,
) -> Generator[AimHook, None, None]:
    """Create an AimHook in state during a pipeline run.

    Args:
        monkeypatch: A pytest monkeypatch fixture.
        kedro_project_with_aim_config: The path to a kedro project with an aim config.
        dummy_pipeline: A dummy pipeline.
        dummy_run_params: Dummy run parameters.
        dummy_catalog: A dummy catalog.

    Yields:
        A AimHook object.
    """
    # change directory to the project
    monkeypatch.chdir(kedro_project_with_aim_config)

    # initialize the project
    bootstrap_project(kedro_project_with_aim_config)

    # create a session
    with KedroSession.create(project_path=kedro_project_with_aim_config) as session:
        context = session.load_context()

        # create hook
        hook = AimHook()

        hook.after_context_created(context)
        hook.after_catalog_created(
            catalog=dummy_catalog,
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
        )
        hook.before_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )

        yield hook

        hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )


@pytest.fixture
def text_datatuple() -> Tuple[AimArtifactDataSet, str]:
    """Create a text artifact dataset and a text string.

    Returns:
        - A text artifact dataset.
        - A text string.
    """
    dataset = AimArtifactDataSet(
        artifact_type=ArtifactType.TEXT,
        name="text_data",
        data_set=dict(
            type="kedro.extras.datasets.text.TextDataSet", filepath="test.md"
        ),
    )
    data = "test"
    return dataset, data


@pytest.fixture
def figure_datatuple() -> Tuple[AimArtifactDataSet, MplFigure]:
    """Create a figure artifact dataset and a figure.

    Returns:
        - A figure artifact dataset.
        - A matplotlib figure.
    """
    dataset = AimArtifactDataSet(
        artifact_type=ArtifactType.FIGURE,
        name="figure_data",
        data_set=dict(
            type="kedro.extras.datasets.pickle.PickleDataSet", filepath="test.pkl"
        ),
    )
    fig = plt.figure()
    plt.plot([1, 2, 3])
    plt.close(fig)
    return dataset, fig


@pytest.fixture
def image_datatuple() -> Tuple[AimArtifactDataSet, MplFigure]:
    """Create an image artifact dataset and an image.

    Returns:
        - An image artifact dataset.
        - A matplotlib figure.
    """
    dataset = AimArtifactDataSet(
        artifact_type=ArtifactType.IMAGE,
        name="image_data",
        data_set=dict(
            type="kedro.extras.datasets.pickle.PickleDataSet", filepath="test.pkl"
        ),
    )
    fig = plt.figure()
    plt.plot([1, 2, 3])
    plt.close(fig)
    return dataset, fig


@pytest.fixture
def audio_datatuple() -> Tuple[AimArtifactDataSet, np.ndarray]:
    """Create an audio artifact dataset and an audio array.

    Returns:
        - An audio artifact dataset.
        - A numpy array.
    """
    dataset = AimArtifactDataSet(
        artifact_type=ArtifactType.AUDIO,
        name="memory_data",
        data_set=dict(
            type="kedro.extras.datasets.pickle.PickleDataSet", filepath="test.pkl"
        ),
    )
    audio_array = np.random.rand(1000)
    return dataset, audio_array


@pytest.fixture
def prefilled_datatuple(tmp_path: Path) -> Tuple[AimArtifactDataSet, str]:
    """Creeate a text artifact dataset and a text string which prefilled data.

    Args:
        tmp_path: The path to a temporary directory.

    Returns:
        - A text artifact dataset.
        - A text string.
    """
    # create a dummy file
    test_data = "test_data"
    test_data_dir = tmp_path / "data.txt"
    with open(test_data_dir, "w") as f:
        f.write(test_data)

    # create a dataset
    dataset = AimArtifactDataSet(
        artifact_type=ArtifactType.TEXT,
        name="test_data",
        data_set=dict(
            type="kedro.extras.datasets.text.TextDataSet", filepath=str(test_data_dir)
        ),
    )
    return dataset, test_data


@pytest.mark.parametrize(
    "datatuple",
    [
        lazy_fixture("text_datatuple"),
        lazy_fixture("figure_datatuple"),
        lazy_fixture("image_datatuple"),
        lazy_fixture("audio_datatuple"),
    ],
)
def test_aim_dataset_save_and_reload_while_run(
    aim_hook_during_run: AimHook,
    datatuple: Tuple[AimArtifactDataSet, Any],
) -> None:
    """Check that save and loads from a aim datasets logs to a aim run.

    Raises:
        ValueError: Unknown artifact type.
    """
    # make dataset
    dataset, data = datatuple
    aim_data_set = make_run_dataset(aim_hook_during_run, dataset)

    # save data and reload it
    aim_data_set._save(data)
    loaded_data = aim_data_set._load()

    # check that data has the same type (Exect match is not possible due save and load)
    assert type(data) == type(loaded_data)

    # check that the data was logged
    assert aim_hook_during_run.run is not None

    # check that the run was properly logged
    metrics = list(list_metrics_in_run(aim_hook_during_run.run))
    metric_names = [metric.name for metric in metrics]
    assert dataset.name in metric_names

    # check stored artifact
    artifact = next(metric for metric in metrics if metric.name == dataset.name)
    value_list = artifact.values.tolist()
    assert len(value_list) == 1
    value = value_list[0]

    if dataset.artifact_type == ArtifactType.TEXT:
        assert isinstance(value, Text)
    elif dataset.artifact_type == ArtifactType.AUDIO:
        assert isinstance(value, Audio)
    elif dataset.artifact_type == ArtifactType.FIGURE:
        assert isinstance(value, Figure)
    elif dataset.artifact_type == ArtifactType.IMAGE:
        assert isinstance(value, Image)
    else:
        raise ValueError(f"Unknown artifact type: {dataset.artifact_type}")


@pytest.mark.parametrize(
    "datatuple",
    [
        lazy_fixture("prefilled_datatuple"),
    ],
)
def test_aim_dataset_logging_at_load(
    aim_hook_during_run: AimHook,
    datatuple: Tuple[AimArtifactDataSet, Any],
) -> None:
    """Check that load from a aim datasets logs to a aim run."""
    # make dataset
    dataset, data = datatuple
    aim_data_set = make_run_dataset(aim_hook_during_run, dataset)

    # only load data
    loaded_data = aim_data_set._load()

    # check that data has the same type (Exect match is not possible due save and load)
    assert type(data) == type(loaded_data)

    # check that the data was logged
    assert aim_hook_during_run.run is not None

    # check that the run was properly logged
    metrics = list(list_metrics_in_run(aim_hook_during_run.run))
    metric_names = [metric.name for metric in metrics]
    assert dataset.name in metric_names


@pytest.mark.parametrize(
    "datatuple",
    [
        lazy_fixture("text_datatuple"),
    ],
)
def test_aim_dataset_save_and_reload_without_run(
    aim_hook_after_catalog_created: AimHook,
    datatuple: Tuple[AimArtifactDataSet, Any],
) -> None:
    """Check that save and loads from a aim datasets without a run does nothing."""
    # make dataset
    dataset, data = datatuple
    aim_data_set = make_run_dataset(aim_hook_after_catalog_created, dataset)

    # save data and reload it
    aim_data_set._save(data)
    loaded_data = aim_data_set._load()

    # check that data has the same type (Exect match is not possible due save and load)
    assert type(data) == type(loaded_data)

    # check that the data was logged
    assert aim_hook_after_catalog_created.run is None
