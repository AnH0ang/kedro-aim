from typing import Generator

from aim import Run
from aim.sdk.query_utils import SequenceView
from aim.sdk.sequence import Sequence


def list_metrics_in_run(run: Run) -> Generator[SequenceView, None, None]:
    """List all metrics in the run.

    HACK: This is a workaround for the `metrics` property of `aim.Run` which is broken.
    In the future, we should use the `metrics` property of `aim.Run` instead of this.

    Args:
        run: A aim run object.

    Yields:
        The metrics that are contained in the run.
    """
    for seq_name, ctx, run in run.iter_sequence_info_by_type("*"):
        yield Sequence(seq_name, ctx, run)  # type: ignore


def list_metrics_names_in_run(run: Run) -> Generator[str, None, None]:
    """List the names of all metrics in the run.

    Args:
        run: A aim run object.

    Yields:
        The names of the metrics that are contained in the run.
    """
    for metric in list_metrics_in_run(run):
        yield metric.name
