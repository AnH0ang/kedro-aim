from enum import Enum
from logging import getLogger
from typing import Any, Dict, Optional

from aim import Audio, Figure, Image, Text
from kedro.io import AbstractDataSet
from kedro.io.core import parse_dataset_definition

from kedro_aim.aim.utils import list_metrics_names_in_run
from kedro_aim.framework import hooks

LOGGER = getLogger(__name__)


class ArtifactType(str, Enum):
    """Enumeration of the artifact types that can be used to tag metrics."""

    IMAGE = "image"
    FIGURE = "figure"
    TEXT = "text"
    AUDIO = "audio"


class AimArtifactDataSet(AbstractDataSet[Any, Any]):
    """A dataset that is used to save artifacts to Aim.

    This dataset does not implement any functionality itself. Instead it is used to
    indicate to the `AimHook` that the artifact should be saved to Aim.
    During the `after_catalog_created` hook, the `AimHook` will replace the dataset
    with the actual dataset that is used to save the artifact to Aim.

    Args:
        artifact_type: The type of the artifact.
        name: The name that is used to save the artifact to Aim.
        data_set: The dataset that is used to load the artifact.
        context: The run context of artifact. Defaults to {}.
        save_args: Additional parameters that are passed to aim. Defaults to None.
    """

    def __init__(
        self,
        artifact_type: ArtifactType,
        name: str,
        data_set: Dict[str, Any],
        context: Dict[str, Any] = {},
        save_args: Optional[Dict[str, Any]] = None,
    ) -> None:
        assert (
            artifact_type in ArtifactType.__members__.values()
        ), f"Invalid artifact type `{artifact_type}`."

        self.artifact_type = artifact_type
        self.data_set = data_set
        self.name = name
        self.context = context
        self.save_args = save_args

    def _load(self) -> Any:  # pragma: no cover
        raise NotImplementedError(
            "This method should be overwritten by `AimArtifactDataSetChild`."
        )

    def _save(self, data: Any) -> None:  # pragma: no cover
        raise NotImplementedError(
            "This method should be overwritten by `AimArtifactDataSetChild`."
        )

    def _describe(self) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError(
            "This method should be overwritten by `AimArtifactDataSetChild`."
        )


def make_run_dataset(
    hook: "hooks.AimHook",
    artifact_dataset: AimArtifactDataSet,
) -> AbstractDataSet[Any, Any]:
    """Takes `AimArtifactDataSet` and replaces it with `AimArtifactDataSetChild`.

    Replacing the dataset is necessary because the `AimArtifactDataSetChild` is the
    actual dataset that is used to save the artifact to Aim. The `AimArtifactDataSet`
    is only used as a placeholder to indicate to the `AimHook` that the artifact should
    be saved to Aim.  This is necessary because we need to wait until the
    `after_catalog_created` hook to pass a reference to the `AimHook` to the dataset.

    Args:
        hook: The `AimHook` hook
        artifact_dataset: The placeholder dataset

    Returns:
        A dataset that is used to save the artifact to Aim.
    """
    data_set_cls, data_set_args = parse_dataset_definition(
        config=artifact_dataset.data_set
    )
    save_args = {} if artifact_dataset.save_args is None else artifact_dataset.save_args

    class AimArtifactDataSetChild(data_set_cls):  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

        def _save(self, data: Any) -> None:
            self._track_artifact(data, artifact_dataset.artifact_type)
            super()._save(data)

        def _load(self) -> Any:
            data = super()._load()

            # track artifact if it was not tracked before
            if hook.run is not None:
                if artifact_dataset.name not in list_metrics_names_in_run(hook.run):
                    self._track_artifact(data, artifact_dataset.artifact_type)

            return data

        def _describe(self) -> Dict[str, Any]:
            return super()._describe()

        @staticmethod
        def _track_artifact(data: Any, artifact_type: ArtifactType) -> None:
            if hook.run is not None:
                if artifact_type == ArtifactType.IMAGE:
                    tracked_data = Image(data, **save_args)
                elif artifact_type == ArtifactType.FIGURE:
                    tracked_data = Figure(data, **save_args)
                elif artifact_type == ArtifactType.TEXT:
                    tracked_data = Text(data, **save_args)
                elif artifact_type == ArtifactType.AUDIO:
                    tracked_data = Audio(data, **save_args)
                else:
                    raise AssertionError(f"Invalid artifact type `{artifact_type}`.")

                hook.run.track(
                    value=tracked_data,
                    name=artifact_dataset.name,
                    context=artifact_dataset.context,  # type: ignore
                )
            else:
                LOGGER.warning("No run is active. Skipping artifact tracking.")

    # rename the class
    parent_name = data_set_cls.__name__
    AimArtifactDataSetChild.__name__ = f"Mlflow{parent_name}"
    AimArtifactDataSetChild.__qualname__ = f"{parent_name}.Mlflow{parent_name}"

    aim_dataset_instance = AimArtifactDataSetChild(**data_set_args)
    return aim_dataset_instance
