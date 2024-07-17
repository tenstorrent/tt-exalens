<div align="center">

<h1>

Debuda

</h1>

A Tenstorent hardware debugger

<img src="./dbd/docs-md/tt_logo.png" alt="ttnn logo" height="150"/>

Works with [PyBuda](https://github.com/tenstorrent/tt-buda) on [Grayskull and Wormhole](https://tenstorrent.com/cards/) cards.

</div>

Debuda is a debugging tool for Tenstorrent's hardware. 
It can be used to access and communicate with the device, or explore bugs and hangs in PyBuda models. 
At the moment, Grayskull and Wormhole devices are supported, while the support for Blackhole cards, as well as support for the Metal runtime are under development.

---

## Building Debuda

### Cloning repository and setting up the environment

After cloning the Debuda repository, be sure to run

```bash
git submodule update --init --recursive
```

so that all the submodules are properly loaded.
It is also a good practice to set `DEBUDA_HOME` environment variable to point to the cloned repository root.

### Requirements

Debuda has been tested on Ubuntu versions 22.04 and 20.04.

[//]: # (TODO: We should check this on vanilla system and also separate test, build and run dependencies, as per #)
To build Debuda, you need the following dependencies:

- software-properties-common,
- build-essential,
- python3.X-venv,
- libyaml-cpp-dev,
- libboost-all-dev,
- libhwloc-dev,
- libzmq3-dev,
- libgtest-dev,
- libgmock-dev,
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

Additional Python dependencies are listed in `dbd/requirements.txt` file, and can be installed via `pip`:

```bash
pip install -r dbd/requirements.txt
```

### Building the library and the application

Once the dependencies are installed, building Debuda should be straightforward, and is done simply by running

```
make build
```

in Debuda home directory.
To be sure that the build was succesful, try running

```bash
python debuda.py
```

in the `DEBUDA_HOME` directory.


## Building and Installing Wheel

Wheel can be installed either from the [GitHub release](https://github.com/tenstorrent/tt-debuda/releases) or built from source.

To build Debuda wheel from source, simply run `make wheel` in the root directory. The installation is then done by running `pip install build/debuda_wheel/<debuda_wheel>.whl`, where `<debuda_wheel>` is an automatically generated name unique for each build.

## Running Debuda

Debuda can be run through `debuda.py` script or by invoking `debuda` command after wheel installation.
There are two basic modes of operation: Limited mode and Buda mode.
Limited mode is entered when no output directory is specified, and it enables basic communication with the device, like writing to and reading from registers or device memory and running .elf files on RISC cores.
Buda mode is invoked by specifying an output directory of PyBuda run.
It enables Debuda access to runtime information, and opens up possibility of using more advanced commands to explore models run on device.

Debuda can run locally or remotely.
For remote runs, a Debuda server is needed.
It can be started either through Debuda application, or from PyBuda runtime.

It is also possible to write all the results from Debuda session to cache, and use them to run Debuda commands again on a system that does not have Tenstorrent hardware.

GDB server can be started from debuda, allowing features like stepping through code and breakpoints to be used through GDB client.

For more information about how to use Debuda, refer to [tutorials](TODO).

## Using Debuda library

Debuda's functionalities can also be used through dbd library to create Python scripts that interact with Tenstorrent's hardware.
For a quick start with dbd library, check out [the tutorial](dbd/docs-md/debuda-lib-tutorial.md).
Full documentation is also available [here](dbd/docs-md/library-docs.md).

## Development

### Testing Debuda

#### Test dependencies

Apart from the base Debuda dependencies, tests require additional python packages:

- pytest,
- coverage,
- parameterized,

which can be installed by running

```bash
pip install -r dbd/test/test_requirements.txt
```

Some tests require using output of a Buda run.
To be able to run those, you need to have a clone of [Budabackend](https://github.com/tenstorrent/tt-budabackend/tree/main), and an environment variable `BUDA_HOME` set to point to the cloned repository.
Tests will build Budabackend in the background and run Buda code on the device so that the output of the run can be used.

#### Running tests

It is currently possible to run tests locally, by running

`./tests/run-all-tests.sh`

from the project root directory. It is also possible to run C++ unit tests with

`make dbdtests`,

and Python unit tests with

`python -m unittest discover -v -t . -s dbd/tests -p *test*.py`.

### Updating documentation

Library documentation is automatically generated through `pydoc-markdown` package.
To update the library docs, you need to have `pydoc-markdown` installed:

```bash
pip install pydoc-markdown
```

and then run

```bash
pydoc-markdown > dbd/docs-md/library-docs.md
```

in the project root.
You can change documentation config through `pydoc-markdown.yml` file.
For more info, see [`pydoc-markdown` project page](https://github.com/NiklasRosenstein/pydoc-markdown).

### Static checks

To be sure that the code passes static checks in the CI pipeline, you can run

```bash
python -m check_copyright --verbose --config infra/copyright-config.yaml 
```

which will add license headers and newlines at file ands where neccessary, and

```bash
./scripts/clang-format-repo.sh
```

which will format C++ files.

---