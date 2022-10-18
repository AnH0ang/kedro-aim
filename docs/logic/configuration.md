# Configuration

## `aim.yml`

The configuration of the module is done via the `aim.yml` config file which is placed in the `conf` folder.
You can generate a default config file by running `kedro aim init` in an existing kedro project and edit it to your needs.
The default config is show below.

```yaml
--8<-- "src/kedro_aim/template/config/aim.yml"
```

The `aim.yml` file contains the following sections:

* `ui`: The UI section contains the configuration of the UI server
* `run`: The run section contains the configuration of the experiment run
* `repository`: The repository section contains the configuration of the repository that is used to store the experiments
* `disable`: The disable section contains the configuration of which parts of the pipeline should be disabled for tracking

## Settings

| Variable                       | Type             | Default     | Description                                                                                                                         |
| ------------------------------ | ---------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `ui.port`                      | `int`            | 43800       | Port to run the aim UI on.                                                                                                          |
| `ui.host`                      | `str`            | `127.0.0.1` | Host to run the aim UI on.                                                                                                          |
| `run.run_hash`                 | `Optional[str]`  | None        | The hash of the run. If a run hash is selected that already exists, it will be logged to that run.                                  |
| `run.experiment`               | `Optional[str]`  | None        | The name of the experiment. 'default’ if not specified. Can be used later to query runs/sequences                                   |
| `run.system_tracking_interval` | `Optional[int]`  | None        | Sets the tracking interval in seconds for system usage metrics (CPU, Memory, etc.). Set to None to disable system metrics tracking. |
| `run.log_system_params`        | `Optional[int]`  | None        | Enable/Disable logging of system params such as installed packages, git info, environment variables, etc.                           |
| `run.capture_terminal_logs`    | `Optional[bool]` | None        | Enable/Disable the capturing of terminal logs.                                                                                      |
| `run.tags`                     | `List[str]`      | []          | List of tags which will be used to tag run.                                                                                         |
| `repository.path`              | `Optional[str]`  | None        | Path to the repository folder.                                                                                                      |
| `repository.read_only`         | `Optional[str]`  | None        | Enable/Disable writes to repository.                                                                                                |
| `repository.init`              | `bool`           | None        | Enable/Disable initialilzation of repository folder before run.                                                                     |
| `disable.pipelines`            | `List[str]`      | []          | List of pipelines in which tracking with aim will be disabled.                                                                      |
