# Contribution

## Project Setup

### Pyenv

In this project we use the python version `3.8.9`. It is recommendet to use Pyenv to install the required Python version as it minimizes conflicts with the system python executable. You can install it using the autoinstaller with the following line.

```bash
curl https://pyenv.run | bash
```

After that you need to install the required python verison `3.8.9`. To do that run:

```bash
pyenv install 3.8.9
```

This command will take a while. After that you should have the binary `python3.8` installed. Pyenv should automatically pick up the right Python version from the `.python-version` file.

### Poetry

Poetry is a tool for dependency management and packaging in Python. It allows you to declare the libraries your project depends on and it will manage (install/update) them for you. To install it run:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

And to force Poetry to install the virtual environment in the project folder, run:

```bash
poetry config virtualenvs.in-project true
```

To install all dependencies and the project itself,
navigate into the folder with the file `poetry.lock`, and execute:

```bash
poetry install
```

## Developement

### Pre-Commit

Pre commit hooks are used to lint the code and to strip output from commited Jupyter Notebooks automatically before every code commit. This assures that only clean code is pushed into the repository. The tool is automatically installed as an dev dependency. To integrate `pre-commit` into your git hooks use `pre-commit install`. To check once against all files `pre-commit run --all-files`. The hooks can be edited in the file `.pre-commit-config.yaml`. You can find more details [here](https://pre-commit.com).

### Commititzen

Commitizen is a tool designed for teams. Its main purpose is to define a standard way of committing rules and communicating it. The tool is automatially installed as a dev dependency.

## Documentation

The code is documented via [mkdocs](https://www.mkdocs.org/) with the extension [mkdosctrings](https://mkdocstrings.github.io/). To generate the documentation the command `mkdocs build` must be used. To open the documentation in the browser the command `mkdocs serve` can be used. To implement new parts of documentation in the report adapt nav section in the `mkdocs.yml` file. A detailed description of the description can be found in the usage description of the mkdocstrings package. To build the documentation a convinience method was registerd with `make`. This can be run with:

```bash
make documentation
```
