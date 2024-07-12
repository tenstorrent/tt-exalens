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

WIP

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

## Development

### Running tests

It is currently possible to run tests locally, by running

`./tests/run-all-tests.sh`

from the project root directory. It is also possible to run C++ unit tests with

`make dbdtests`,

and Python unit tests with

`python -m unittest discover -v -t . -s dbd/tests -p *test*.py`.

Be sure to have a virtual environment with all dependencies from `dbd/tests/test-requirements.txt` installed.

---