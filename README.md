<div align="center">

<h1>

Debuda

</h1>

A low level hardware debugger

<img src="./dbd/docs-md/tt_logo.png" alt="ttnn logo" height="100"/>

</div>
<br/>

Debuda is a low level debugging tool for Tenstorrent's hardware.
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

`./test/run-all-tests.sh`

from the project root directory. It is also possible to run C++ unit tests with

`make dbdtests`,

and Python unit tests with

`python -m unittest discover -v -t . -s dbd/tests -p *test*.py`.

Be sure to have a virtual environment with all dependencies from `dbd/tests/test-requirements.txt` installed.

---




## Troubleshooting

### No rule to make target 'third_party/umd/device/module.mk'
```
> make test
Makefile:178: third_party/umd/device/module.mk: No such file or directory
make: *** No rule to make target 'third_party/umd/device/module.mk'.  Stop.
```
Fix:
```
git submodule update --init --recursive
```

### Error: DEBUDA_HOME is not set. Please set DEBUDA_HOME to the root of the debuda repository

```
> make test
Error: DEBUDA_HOME is not set. Please set DEBUDA_HOME to the root of the debuda repository
make: *** [Makefile:182: test] Error 1
...
Error: BUDA_HOME is not set. Please set BUDA_HOME to the root of the budabackend repository
make: *** [Makefile:182: test] Error 1
```
Fix:
```
export DEBUDA_HOME=`pwd`
export BUDA_HOME=~/work/bbe
```

### fatal error: zmq.hpp: No such file or directory

```
In file included from dbd/server/lib/inc/dbdserver/server.h:8,
                 from dbd/server/app/debuda-server-standalone.cpp:11:
dbd/server/lib/inc/dbdserver/communication.h:9:10: fatal error: zmq.hpp: No such file or directory
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