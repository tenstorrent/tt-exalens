<div align="center">
<h1> TTLens </h1>
  
A low level hardware debugger

<img src="./docs/images/tt_logo_stacked_color.png" alt="ttnn logo" height="100"/>

</div>
<br/>

TTLens is a low level debugging tool for Tenstorrent's hardware.
It can be used to access and communicate with the device, or explore bugs and hangs in PyBuda models.
At the moment, Grayskull and Wormhole devices are supported, while the support for Blackhole cards, as well as support for the Metal runtime are under development.

---

## Building TTLens

### Cloning repository and setting up the environment

After cloning the TTLens repository, be sure to run

```bash
git submodule update --init --recursive
```

so that all the submodules are properly loaded.

### Requirements

TTLens has been tested on Ubuntu versions 22.04 and 20.04.

[//]: # (TODO: We should check this on vanilla system and also separate test, build and run dependencies, as per #)
To build TTLens, you need the following dependencies:

- software-properties-common,
- build-essential,
- python3.X-venv,
- libyaml-cpp-dev,
- libboost-all-dev,
- libhwloc-dev,
- libzmq3-dev,
- xxd,

which can be installed by running

```bash
sudo apt install software-properties-common build-essential libyaml-cpp-dev libboost-all-dev libhwloc-dev libzmq3-dev libgtest-dev libgmock-dev xxd
```

Both python 3.8 and 3.10 are actively supported, so you can use either

```bash
sudo apt install python3.8-venv
```

or

```bash
sudo apt install python3.10-venv
```

depending on Python version available on your system.

Additional Python dependencies are listed in `ttlens/requirements.txt` file, and can be installed via `pip`:

```bash
pip install -r ttlens/requirements.txt
```

### Building the library and the application

Once the dependencies are installed, building TTLens should be straightforward, and is done simply by running

```
make build
```

in TTLens home directory.
To be sure that the build was succesful, try running

```bash
python tt-lens.py
```

or

```bash
./tt-lens.py
```

in the root directory.


## Building and Installing Wheel

Wheel can be installed either from the [GitHub release](https://github.com/tenstorrent/tt-debuda/releases), built from source, or installed directly from GitHub with
```
pip install git+https://github.com/tenstorrent/tt-debuda.git
```

To build TTLens wheel from source, simply run `make wheel` in the root directory. The installation is then done by running `pip install build/ttlens_wheel/<ttlens_wheel>.whl`, where `<ttlens_wheel>` is an automatically generated name unique for each build.

## Running TTLens

TTLens can be run through `tt-lens.py` script or by invoking `ttlens` command after wheel installation.
There are two basic modes of operation: Limited mode and Buda mode.
Limited mode is entered when no output directory is specified, and it enables basic communication with the device, like writing to and reading from registers or device memory and running .elf files on RISC cores.
Buda mode is invoked by specifying an output directory of PyBuda run.
It enables TTLens access to runtime information, and opens up possibility of using more advanced commands to explore models run on device.

TTLens can run locally or remotely.
For remote runs, a TTLens server is needed.
It can be started either through TTLens application, or from PyBuda runtime.

It is also possible to write all the results from TTLens session to cache, and use them to run TTLens commands again on a system that does not have Tenstorrent hardware.

GDB server can be started from TTLens, allowing features like stepping through code and breakpoints to be used through GDB client.

For more information about how to use the TTLens application, refer to [the tutorial](./docs/ttlens-app-tutorial.md), or [the documentation](./docs/ttlens-app-docs.md).

## Using TTLens library

TTLens's functionalities can also be used through ttlens library to create Python scripts that interact with Tenstorrent's hardware.
For a quick start with ttlens library, check out [the tutorial](docs/ttlens-lib-tutorial.md).
Full documentation is also available [here](docs/ttlens-lib-docs.md).

## Development

### Testing TTLens

#### Test dependencies

Apart from the base TTLens dependencies, tests require additional python packages:

- pytest,
- coverage,
- parameterized,

and system libraries:

- libgtest-dev,
- libgmock-dev,

which can be installed by running

```bash
pip install -r test/test_requirements.txt
```

Some tests require using output of a Buda run.
To be able to run those, you need to have a clone of [Budabackend](https://github.com/tenstorrent/tt-budabackend/tree/main), and an environment variable `BUDA_HOME` set to point to the cloned repository.
Tests will build Budabackend in the background and run Buda code on the device so that the output of the run can be used.

#### Running tests

It is currently possible to run tests locally, by running

`make test`

from the project root directory.

### Updating documentation

Library documentation is automatically generated from source code docstrings.
To update the library docs, you need to run:

`make docs`

in the project root.
For more advanced use cases, refer to the source code of the documentation generation scripts, located in `docs/bin`.

### Static checks

To be sure that the code passes static checks in the CI pipeline, you can run

```bash
pip install -r ./infra/requirements-infra.txt
python -m check_copyright --verbose --config infra/copyright-config.yaml 
```

which will add license headers and newlines at file ands where neccessary, and

```bash
./scripts/clang-format-repo.sh
```

which will format C++ files.

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
In file included from ttlens/server/lib/inc/ttlensserver/server.h:8,
                 from ttlens/server/app/ttlens-server-standalone.cpp:11:
ttlens/server/lib/inc/ttlensserver/communication.h:9:10: fatal error: zmq.hpp: No such file or directory
    9 | #include <zmq.hpp>
```

This happens when the docker image does not contain the required dependencies.
Fix:
```
sudo apt update && sudo apt-get install -y libzmq3-dev libboost-all-dev libgtest-dev libgmock-dev
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



### ModuleNotFoundError: No module named 'ttlens_pybind_unit_tests'

This error might occur when trying to run unit tests:
```
Failed to import test module: test.ttlens.pybind.test_bindings
Traceback (most recent call last):
  File "/usr/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/dcvijetic/work/tt-debuda/test/ttlens/pybind/test_bindings.py", line 17, in <module>
    from ttlens_pybind_unit_tests import set_ttlens_test_implementation
ModuleNotFoundError: No module named 'ttlens_pybind_unit_tests'
```
To fix, just build the neccessary test library:
```
make build
```
