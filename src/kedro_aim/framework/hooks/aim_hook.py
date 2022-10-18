from enum import Enum
from logging import getLogger
from typing import Any, Dict, Optional

from aim import Run
from kedro.config import MissingConfigException
from kedro.framework.context import KedroContext
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

from kedro_aim.config import KedroAimConfig
from kedro_aim.config.utils import load_repository
from kedro_aim.framework.hooks.utils import check_aim_enabled
from kedro_aim.io.artifacts import AimArtifactDataSet, make_run_dataset

LOGGER = getLogger(__name__)


class StatusTag(str, Enum):
    """Enumeration of the status tags that can be used to tag metrics."""

    FAILURE = "failure"
    SUCCESS = "success"


class AimHook:
    """The hook that is used to integrate Aim with Kedro.

    The hook is responsible for:

    - Creating the Aim run before the pipeline is run.
    - Adding the Aim run to the catlog.
    """

    run: Optional[Run] = None
    aim_confg: KedroAimConfig

    @hook_impl
    def after_context_created(
        self,
        context: KedroContext,
    ) -> None:
        """Hooks to be invoked after a `KedroContext` is created.

        This hook reads the Aim configuration from the `aim.yml` from the `conf` folder
        of the Kedro project and stores it in the `aim_config` attribute of the hook.

        Args:
            context: The newly created context.
        """
        # Find the AimConfig in the context
        try:
            conf_aim_yml = context.config_loader.get("aim*", "aim*/**")
        except MissingConfigException:
            LOGGER.warning("No 'aim.yml' config file found in environment")
            conf_aim_yml = {}
        aim_config = KedroAimConfig.parse_obj(conf_aim_yml)

        # store in context for interactive use
        context.__setattr__("aim", aim_config)

        # store for further reuse
        self.aim_config = aim_config

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
        """Hooks to be invoked after a data catalog is created.

        Im this hook we go through all the datasets in the catalog an replace the
        datasets that are of type `AimArtifactDataSet` with a special aim dataset.

        Args:
            catalog: The catalog that was created.
            conf_catalog: The config from which the catalog was created.
            conf_creds: The credentials conf from which the catalog was created.
            feed_dict: The feed_dict that was added to the catalog after creation.
            save_version: The save_version used in `save` operations
                for all datasets in the catalog.
            load_versions: The load_versions used in `load` operations
                for each dataset in the catalog.
        """
        # HACK: Replace all AimArtifactDataSet with a AimArtifactDataSetChild dataset.
        # This is needed to pass a reference of the run to the dataset.
        for name, dataset in catalog._data_sets.items():
            if isinstance(dataset, AimArtifactDataSet):
                catalog._data_sets[name] = make_run_dataset(self, dataset)

    @hook_impl
    def before_pipeline_run(
        self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog
    ) -> None:
        """Hook to be invoked before a pipeline runs.

        Before the pipeline runs, we create the Aim run and add it to the catalog
        under the name `run`. This allows us to access the run in the pipeline.

        Args:
            run_params: The params used to run the pipeline.
                Should have the following schema

                ```
                   {
                     "session_id": str
                     "project_path": str,
                     "env": str,
                     "kedro_version": str,
                     "tags": Optional[List[str]],
                     "from_nodes": Optional[List[str]],
                     "to_nodes": Optional[List[str]],
                     "node_names": Optional[List[str]],
                     "from_inputs": Optional[List[str]],
                     "to_outputs": Optional[List[str]],
                     "load_versions": Optional[List[str]],
                     "pipeline_name": str,
                     "extra_params": Optional[Dict[str, Any]]
                   }
                ```

            pipeline: The `Pipeline` that will be run.
            catalog: The `DataCatalog` to be used during the run.
        """
        if check_aim_enabled(run_params["pipeline_name"], self.aim_config):
            # Create the Aim Run
            self.run = Run(
                run_hash=self.aim_config.run.run_hash,
                repo=load_repository(self.aim_config.repository),
                experiment=self.aim_config.run.experiment,
                system_tracking_interval=self.aim_config.run.system_tracking_interval,
                log_system_params=self.aim_config.run.log_system_params,
                capture_terminal_logs=self.aim_config.run.capture_terminal_logs,
            )

            # log run paramerters
            self.run["kedro"] = run_params

            # add tags
            for tag in self.aim_config.run.tags:
                self.run.add_tag(tag)

            # save run in catalog
            assert not catalog.exists("run"), "catalog already contains a 'run' dataset"
            catalog.add("run", MemoryDataSet(copy_mode="assign"))
            catalog.save("run", self.run)

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        catalog: DataCatalog,
        inputs: Dict[str, Any],
        is_async: bool,
        session_id: str,
    ) -> None:
        """Hook to be invoked before a node runs.

        All `parameters` that are passed to the node are logged to the run.

        Args:
            node: The `Node` to run.
            catalog: A `DataCatalog` containing the node's inputs and outputs.
            inputs: The dictionary of inputs dataset.
                The keys are dataset names and the values are the actual loaded input
                data, not the dataset instance.
            is_async: Whether the node was run in `async` mode.
            session_id: The id of the session.
        """
        if self.run is not None:
            # only parameters will be logged.
            for k, v in inputs.items():
                if k.startswith("params:"):
                    self.run[k[7:]] = v
                elif k == "parameters":
                    self.run[k] = v

    @hook_impl
    def after_pipeline_run(
        self,
        run_params: Dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ) -> None:
        """Hook to be invoked after a pipeline runs.

        After the pipeline runs, we close the Aim run and add `StatusTag.SUCCESS` tag.

        Args:
            run_params: The params used to run the pipeline.
                Should have the following schema

                ```
                   {
                     "session_id": str
                     "project_path": str,
                     "env": str,
                     "kedro_version": str,
                     "tags": Optional[List[str]],
                     "from_nodes": Optional[List[str]],
                     "to_nodes": Optional[List[str]],
                     "node_names": Optional[List[str]],
                     "from_inputs": Optional[List[str]],
                     "to_outputs": Optional[List[str]],
                     "load_versions": Optional[List[str]],
                     "pipeline_name": str,
                     "extra_params": Optional[Dict[str, Any]]
                   }
                ```

            pipeline: The `Pipeline` that was run.
            catalog: The `DataCatalog` used during the run.
        """
        if self.run is not None:
            self.run.add_tag(StatusTag.SUCCESS)
            self.run.finalize()
            self.run.close()

    @hook_impl
    def on_pipeline_error(
        self,
        error: Exception,
        run_params: Dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ) -> None:
        """Hook to be invoked if a pipeline run throws an uncaught Exception.

        In this case, we close the run and add a `StatusTag.FAILURE` tag.

        Args:
            error: The uncaught exception thrown during the pipeline run.
            run_params: The params used to run the pipeline.
                Should have the following schema

                ```
                   {
                     "session_id": str
                     "project_path": str,
                     "env": str,
                     "kedro_version": str,
                     "tags": Optional[List[str]],
                     "from_nodes": Optional[List[str]],
                     "to_nodes": Optional[List[str]],
                     "node_names": Optional[List[str]],
                     "from_inputs": Optional[List[str]],
                     "to_outputs": Optional[List[str]],
                     "load_versions": Optional[List[str]],
                     "pipeline_name": str,
                     "extra_params": Optional[Dict[str, Any]]
                   }
                ```
            pipeline: The ``Pipeline`` that will was run.
            catalog: The ``DataCatalog`` used during the run.
        """
        if self.run is not None:
            self.run.add_tag(StatusTag.FAILURE)
            self.run.finalize()
            self.run.close()


aim_hook = AimHook()
