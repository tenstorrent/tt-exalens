<div align="center">
<h1> TT-Lensium :tm: </h1>

A low level hardware debugger

<img src="./docs/images/tt_logo_stacked_color.png" alt="ttnn logo" height="100"/>

</div>
<br/>

This is a low-level debugging tool for Tenstorrent hardware.
It enables access to and communication with the device.
It supports Wormhole and Blackhole devices.

---

## Quickstart

The wheel can be installed directly from GitHub with:
```
pip install git+https://github.com/tenstorrent/tt-exalens.git
```

The CLI application can be run by invoking `tt-exalens` command after installing the wheel.

## Building

### Cloning repository and setting up the environment

After cloning the repository, run:

```bash
git submodule update --init --recursive
```

to ensure all submodules are properly initialized.

### Requirements

Project has been tested on Ubuntu 22.04.

To build it, you need the following dependencies:

- software-properties-common,
- build-essential,
- python3.X-venv,
- libyaml-cpp-dev,
- libhwloc-dev,
- libzmq3-dev,
- xxd,
- ninja-build

Install them with:

```bash
sudo apt install software-properties-common build-essential libyaml-cpp-dev libhwloc-dev libzmq3-dev libgtest-dev libgmock-dev xxd ninja-build
```

Python 3.10 is the only supported version. Install it with:

```bash
sudo apt install python3.10-venv
```

Additional Python dependencies are listed in `ttexalens/requirements.txt` and can be installed with:

```bash
pip install -r ttexalens/requirements.txt
```

### Building the library and the application

Once the dependencies are installed, building the project is straightforward and can be done by running:

```
make build
```

from the project's root directory.

To verify that the build was successful, try running:

```bash
python tt-exalens.py
```

or

```bash
./tt-exalens.py
```

from the root directory.


## Building and Installing Wheel

The wheel can be installed from the [GitHub release](https://github.com/tenstorrent/tt-exalens/releases), built from source, or installed directly from GitHub with
```
pip install git+https://github.com/tenstorrent/tt-exalens.git
```

Another option is to build the wheel from local source, run:
```
make wheel
```
in the root directory. Then install it using:
```
pip install build/ttexalens_wheel/<ttexalens_wheel>.whl
```
where `<ttexalens_wheel>` is an automatically generated filename for the build.

## Running the CLI application

The CLI application can be run via the `tt-exalens.py` script or by invoking `tt-exalens` command after installing the wheel.
It currently operates in *Limited* mode by default, with plans to support additional modes in the future.
Limited mode allows basic communication with the device, such as reading/writing registers and memory, and running `.elf` files on RISC cores.

The CLI application can target local or remote devices.
For remote runs, a server instance is required and can be started using the same application.

It’s also possible to cache session results and replay commands on a machine without Tenstorrent hardware.

A GDB server can be launched, enabling stepping, breakpoints, and other debugging features via a GDB client.

For more usage information, refer to [the tutorial](./docs/ttexalens-app-tutorial.md) or [the documentation](./docs/ttexalens-app-docs.md).

## Using library

The application functionalities can also be accessed through the `ttexalens` Python library to create scripts that interact with Tenstorrent hardware.

For a quick start with the library, check out [the tutorial](docs/ttexalens-lib-tutorial.md).
Full documentation is also available [here](docs/ttexalens-lib-docs.md).

## Development

### Testing

#### Test dependencies

Apart from the base dependencies, running tests requires additional Python packages:

- `pytest`
- `coverage`
- `parameterized`

and system libraries:

- `libgtest-dev`
- `libgmock-dev`

Install the Python packages with:

```bash
pip install -r test/test_requirements.txt
```

#### Running tests

It is currently possible to run tests locally, by running

`make test`

from the project root directory.

### Updating documentation

In order to update documentation virtual environment has to be created first by running the following command:

```bash
./scripts/create-venv.sh
```

To activate created environment use

```bash
.venv/bin/activate
```

Library documentation is automatically generated from source code docstrings.
To update the library docs, you need to run (while in created environment):

`make docs`

in the project root.
For more advanced use cases, refer to the source code of the documentation generation scripts, located in `docs/bin`.

### Static checks

#### Pre-commit

We have defined various pre-commit hooks that check the code for formatting, licensing issues, etc.

To install pre-commit , run the following command:

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

### Updating docker images

To update docker images used on CI and in development, you need to update Dockerfiles in `.github` directory and then run [`release-docker-images`](.github/workflows/release-docker-images.yaml) workflow.
This can be done through GitHub CLI (see [here](https://github.com/cli/cli?tab=readme-ov-file#linux--bsd) how to install it) by using command

```bash
gh workflow run 116548537 --ref <your-branch-name>
```

This will automatically generate new image releases and tag them as `latest`.

---




## Troubleshooting

### fatal error: zmq.hpp: No such file or directory

```
In file included from ttexalens/server/lib/inc/ttexalensserver/server.h:8,
                 from ttexalens/server/app/ttexalens-server-standalone.cpp:11:
ttexalens/server/lib/inc/ttexalensserver/communication.h:9:10: fatal error: zmq.hpp: No such file or directory
    9 | #include <zmq.hpp>
```

This happens when the docker image does not contain the required dependencies.
Fix:
```
sudo apt update && sudo apt-get install -y libzmq3-dev libgtest-dev libgmock-dev
```


### python: command not found
```
test/wheel-test/wheel-test.sh: line 11: python: command not found
make: *** [Makefile:182: test] Error 127
```
Fix:
```
alias python=python3
```



### ModuleNotFoundError: No module named 'ttexalens_pybind_unit_tests'

This error might occur when trying to run unit tests:
```
Failed to import test module: test.ttexalens.pybind.test_bindings
Traceback (most recent call last):
  File "/usr/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "./test/ttexalens/pybind/test_bindings.py", line 17, in <module>
    from ttexalens_pybind_unit_tests import set_ttexalens_test_implementation
ModuleNotFoundError: No module named 'ttexalens_pybind_unit_tests'
```
To fix, just build the neccessary test library:
```
make build
```
