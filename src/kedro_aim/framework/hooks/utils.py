from kedro_aim.config import KedroAimConfig


def check_aim_enabled(pipeline_name: str, aim_config: KedroAimConfig) -> bool:
    """Check if Aim is enabled for the given pipeline.

    Args:
        pipeline_name: Name of the pipeline.
        aim_config: Kedro-Aim configuration.

    Returns:
        A boolean indicating whether Aim is enabled for the given pipeline.
    """
    return pipeline_name not in aim_config.disable.pipelines
