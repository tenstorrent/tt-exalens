# Buda Debug Interface and Tools

## General Information

[Documentation](https://tenstorrent.sharepoint.com/:f:/r/sites/Specifications/Spatial/Debug?csf=1&web=1&e=m6PtgT]) on Sharepoint:
- [Debug architecture](https://tenstorrent.sharepoint.com/:w:/r/sites/Specifications/Spatial/Debug/buda_debug_architecture.docx?d=w314badcf8d404f4b92e083091b0edad5&csf=1&web=1&e=EEX4UD)
- [Presentation](https://tenstorrent.sharepoint.com/:p:/r/sites/Specifications/Spatial/Debug/buda-debug-infra.pptx?d=wb835600fe80c44b79831eecb58290533&csf=1&web=1&e=r6m3Ux)

Source code path: **dbd/**.
Main development branch: **ihamer/debuda**.

List of all [Debuda issues](https://yyz-gitlab.local.tenstorrent.com/tenstorrent/budabackend/-/issues?scope=all&state=opened&label_name[]=Debuda). Gitlab issues label: **debuda**.

`slack`: #debuda

## Debuda.py

Debuda.py can be used to probe the state of a Buda run in silicon. Currently, it can show
details of NOC state, and status of various Queues (DRAM, Host, Epoch). It can also be used
to do random NOC reads (in case one knows the exact address of a register or memory location).
It can analyze the status of all streams and report any that appear hung.

The implementation consists of two parts: the client (debuda.py) and the debug server (debuda-stub). The two communicate over TCP using [ZeroMQ](https://zeromq.org/) messaging library.

![High level diagram](dbd/docs/images/debuda.png)

### Usage

Install dependencies:
```
sudo apt update && sudo apt install -y libzmq3-dev
pip install pyzmq tabulate
```

Run something on the device (for example):
```
make verif/op_tests
./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --seed 0 --silicon --timeout 500
```

Run debuda.py:
```
python3 device/bin/silicon/debuda.py  tt_build/test_op_6142509188972423790 --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml
```
Debuda.py will read necessary files (e.g. netlist, blob/pipegen.yaml), and perform initial
probing of the queues which shows presents any anomalies (such as queues with non-zero
 occupancy).

The program then enters a REPL (read-evaluate-print-loop) which allows one to interactively
issue further commands. These commands allow one to trace the graph on the device

![Start and REPL](dbd/docs/images/debuda-start-and-repl.png)

For more information about the REPL, see below.

`--commands` argument:

Use **--commands** to supply a semicolon-separated list of commands to execute immediately. This
can be useful when interactive (REPL) mode is not desirable. If **exit** is supplied as the last
command, Debuda.py will terminate. As an example:

```
python3 device/bin/silicon/debuda.py  tt_build/test_op_6142509188972423790 --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --commands "s 1 1 24;exit"
```
The above command will show Stream 24 on core 1-1 and then terminate.

### REPL

`Help`

Enter **help** (or any other invalid command) to see the list of available commands

`Speed Dial`

Occasionally, the program will present a list of commands that can be executed by
entering a single digit only. For example, when looking at a core, the speed
dial will show commands to jump to any destination or source streams connected to the core.

![Speed Dial](dbd/docs/images/debuda-speed-dial.png)

In the above screenshot, sources and destinations of the currently selected core are shown. The currently selected stream (stream 8 of core 1-1) is highlighted in red. To quickly jump to the
source of the current stream, one can enter `0`.

## Miscellaneous

### Building debuda-stub
```
bin/build-debuda-stub.sh
```
Prebuilt binary is committed to git repo for convenience.
