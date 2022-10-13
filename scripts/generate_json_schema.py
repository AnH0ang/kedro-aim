from pathlib import Path

import click

from kedro_aim.config import KedroAimConfig

DEFAULT_DESTINATION = Path("static/jsonschema/kedro_aim_schema.json")


@click.command()
@click.option(
    "--destination",
    "-d",
    required=False,
    default=DEFAULT_DESTINATION,
    type=click.Path(path_type=Path),
    help="Path to the directory where the schema will be saved.",
)
def main(destination: Path) -> None:
    """Generate the json schema for the `aim.yml` from the KedroAimConfig class."""
    with open(destination, "w") as f:
        schema_str = KedroAimConfig.schema_json(indent=2)
        f.write(schema_str)
        f.write("\n")


if __name__ == "__main__":
    main()
