<div align="center">
<h1> TT-Lensium :tm: </h1>

A low-level hardware debugger

<img src="./docs/images/tt_logo_stacked_color.png" alt="ttnn logo" height="100"/>

</div>
<br/>

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/tenstorrent/tt-exalens) [![PyPI](https://img.shields.io/pypi/v/tt-exalens?color=green)](https://pypi.org/project/tt-exalens/)

A low-level debugging tool for Tenstorrent hardware that enables direct access to and communication with Wormhole and Blackhole devices.

---

## Quickstart

You can install latest published version with:
```
pip install tt-exalens
```
Or specific version with:
```
pip install tt-exalens=="x.y.z"
```

Alternatively, you can install the latest code from GitHub with:
```
pip install git+https://github.com/tenstorrent/tt-exalens.git
```

The CLI application can be run by invoking the `tt-exalens` command after installing the wheel.

## Running the CLI application

The CLI application can be run via the `tt-exalens.py` script or by invoking the `tt-exalens` command after installing the wheel.

The application supports both local and remote device access.
For remote connections, a server instance must be started using the same application.

A GDB server can be launched, enabling stepping, breakpoints, and other debugging features via a GDB client.

For more usage information, refer to [the tutorial](./docs/ttexalens-app-tutorial.md) or [the documentation](./docs/ttexalens-app-docs.md).

## Using library

The application functionality is also available through the `ttexalens` Python library, enabling you to create custom scripts that interact with Tenstorrent hardware.

For a quick start with the library, check out [the tutorial](docs/ttexalens-lib-tutorial.md).
Full documentation is also available [here](docs/ttexalens-lib-docs.md).

## Development

### Setting up environment

The recommended way to manage dependencies is by creating a virtual environment with:

```bash
./scripts/create-venv.sh
```

To activate the created environment, use:

```bash
.venv/bin/activate
```

Alternatively, you can use your existing environment and just install dependencies with:

```bash
./scripts/install-deps.sh
```

### Testing

#### Test requirements

The following dependencies are required to build the necessary kernels:

- ninja-build,
- cmake
- make

#### Running tests

The easiest way to run all tests locally is by using the `make` wrapper from the project root directory:

```bash
make test
```

This command will build dependencies, run all tests, create the wheel, and run wheel tests.

If you don't need all of these steps, you can run them manually:

```bash
# Compile kernels that tests use
make

# Install runtime dependencies
pip install -r ttexalens/requirements.txt

# Install test dependencies
pip install -r test/test_requirements.txt

# Run library tests
pytest test/ttexalens

# Run CLI application tests
pytest test/app
```

If you're developing with VSCode (or its derivatives), you can use the Testing extension. Install the `Python` extension to enumerate all tests within the `Testing` tab in the activity bar.

### Updating documentation

Library documentation is automatically generated from source code docstrings.
To update the library documentation, run the following command in your development environment:

`make docs`

in the project root.
For more advanced use cases, refer to the source code of the documentation generation scripts, located in `docs/bin`.

### Static checks

#### Pre-commit

We have defined various pre-commit hooks that check the code for formatting, licensing issues, etc.

To install pre-commit, run the following command:

```sh
pip install pre-commit
```

After installing pre-commit, you can install the hooks by running:

```sh
pre-commit install
```

Now, each time you run `git commit` the pre-commit hooks (checks) will be executed.

If you have already committed before installing the pre-commit hooks, you can run on all files to "catch up":

```sh
pre-commit run --all-files
```

For more information visit [pre-commit](https://pre-commit.com/)

#### mypy

We use [mypy](https://mypy.readthedocs.io) for static code analysis.

You can use the `make` wrapper to execute it with:

```bash
make mypy
```

Or run it directly from your development environment with:

```bash
mypy
```
