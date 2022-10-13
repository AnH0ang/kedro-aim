from pathlib import Path
from typing import Any, Union

from jinja2 import Environment, FileSystemLoader


def render_jinja_template(
    src: Union[str, Path], is_cookiecutter: bool = False, **kwargs: Any
) -> str:  # pragma: no cover
    """Render a template file and replace tis jinja's tags.

    This functions enable to copy a file and render the tags (identified by
    `{{ my_tag }}`) with the values provided in kwargs.

    Args:
        src:  The path to the template which should be rendered
        is_cookiecutter: If the template is a cookiecutter template
        **kwargs: Extra arguments to be passed to the template

    Returns:
        A string that contains all the files with replaced tags.
    """
    src = Path(src)

    template_loader = FileSystemLoader(searchpath=src.parent.as_posix())
    # the keep_trailing_new_line option is mandatory to
    # make sure that black formatting will be preserved
    template_env = Environment(loader=template_loader, keep_trailing_newline=True)
    template = template_env.get_template(src.name)
    if is_cookiecutter:
        # we need to match tags from a cookiecutter object
        # but cookiecutter only deals with folder, not file
        # thus we need to create an object with all necessary attributes
        class FalseCookieCutter:
            def __init__(self, **kwargs: Any) -> None:
                self.__dict__.update(kwargs)

        parsed_template = template.render(cookiecutter=FalseCookieCutter(**kwargs))
    else:
        parsed_template = template.render(**kwargs)

    return parsed_template


def write_jinja_template(
    src: Union[str, Path], dst: Union[str, Path], **kwargs: Any
) -> None:
    """Write a template file and replace tis jinja's tags.

    Write a template file and replace tis jinja's tags (identified by `{{ my_tag }}`)
    with the values provided in kwargs.

    Args:
        src: Path to the template which should be rendered
        dst: Path where the rendered template should be saved
        **kwargs: Extra arguments to be passed to the template
    """
    dst = Path(dst)
    parsed_template = render_jinja_template(src, **kwargs)
    with open(dst, "w") as file_handler:
        file_handler.write(parsed_template)
