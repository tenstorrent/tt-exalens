# Buda Debug Interface and Tools

## General Information

[Documentation](https://tenstorrent.sharepoint.com/:f:/r/sites/Specifications/Spatial/Debug?csf=1&web=1&e=m6PtgT]) on Sharepoint:
- [Debug architecture](https://tenstorrent.sharepoint.com/:w:/r/sites/Specifications/Spatial/Debug/buda_debug_architecture.docx?d=w314badcf8d404f4b92e083091b0edad5&csf=1&web=1&e=EEX4UD)
- [Presentation](https://tenstorrent.sharepoint.com/:p:/r/sites/Specifications/Spatial/Debug/buda-debug-infra.pptx?d=wb835600fe80c44b79831eecb58290533&csf=1&web=1&e=r6m3Ux)

Source code path: **dbd/**.
Main development branch: **ihamer/debuda**.

List of all [Debuda issues](https://yyz-gitlab.local.tenstorrent.com/tenstorrent/budabackend/-/issues?scope=all&state=opened&label_name[]=Debuda). Gitlab issues label: **debuda**.

[CI Dashboard](http://yyz-elk/goto/e8be9082b7cc6682fd692f4a5ec5f1e1)
[CI last two days](http://yyz-elk/goto/af8e4fe5b9afc69533e2b9bc9259f114)

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
pip install pyzmq tabulate prompt_toolkit
```

Run something on the device (for example):
```
make verif/op_tests
./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --seed 0 --silicon --timeout 500
```

Run debuda.py:
```
dbd/debuda.py  tt_build/test_op_6142509188972423790 --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml
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
dbd/debuda.py  tt_build/test_op_6142509188972423790 --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --commands "s 1 1 24;exit"
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

## Offline use (--server-cache)

It is sometimes desirable to run debuda without having a connection to a running device. For this purpose, Debuda can use a cache file. An example usage scenario could be:


- A customer runs Debuda with `--server-cache through` and sends the resulting cache file to Tenstorrent for debugging
- A Tenstorrent engineer uses Debuda locally with `--server-cache on` to load the cache file and debug the design.

Note: not all commands will be available to Tenstorrent engineer. Naturally, any command that writes to the device will not accomplish much. Any command that reads from an area of the device that was not cached will also fail. Therefore, the customer run of Debuda should read from all the relevant device areas as that will store those areas in the cache.

Currently, this functionality is supported through a fairly manual flow (perhaps by using --commands for some automation). In the future, the feature will be expanded to automatically dump all relevant chip areas (DRAM, L1, registers...)

## Miscellaneous

### Building debuda-stub
```
bin/build-debuda-stub.sh
```
Prebuilt binary is committed to git repo for convenience.

## High Level Debugging

While debuda can help find low level bugs on silicon, High Level Debugging (aka Tapout Sweep) is used to find data mismatch errors. It runs a netlist iteratively with each operation 'tapped out' in topological order. The result of the tapped-out operation is compared with the golden results. Two flows are supported: budabackend and pybuda.

### Usage

From BudaBackEnd:
```
dbd/tapout_sweep.py --test_command "command" --out_dir output

ex.
dbd/tapout_sweep.py --test_command "build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --seed 0 --silicon --timeout 500" --out_dir tapout_output
```

From PyBuda:
```
dbd/pybuda_tapout_sweep.py "pytest_command" --out_dir output

ex.
dbd/pybuda_tapout_sweep.py "pytest -svv ../../pybuda/test/backend/test_bert.py::test_encoder[inference-Grayskull-cfg0-no_recompute]" --out_dir debuda_temp
```
### How it works
It runs the provided command a number of times. Each time, it modifies the netlist by adding a DRAM queue to the output of a particular operation. This makes the result of the operation observable and comparable to golden restults. The output of the command log is examined and PASS/FAIL condition printed. Currently, the only supported command for parsing output and automatically providing correctness of operations is ***verif/op_tests/test_op***. If the output of the operation does not match golden results, the Op will be logged as failed. The Log is stored in "<span style="color:green">output_directory/tapout_result.log</span>". An entry in this file looks like this:
```
	Command: build/test/verif/op_tests/test_op --seed 0 --silicon --timeout 500 --netlist tapout_output/fwd_0_norm_ff_0_recip.yaml --pytorch-bin /home/ihamer/work/pybuda/third_party/budabackend/tapout_output/pybuda_test_backend_test_bert_py_test_encoder_inference-Grayskull-cfg0-no_recompute
	Log:tapout_output/fwd_0_norm_ff_0_recip.log
op_name: norm_ff_0_recip_s_brcst_m1_0_0.lc1
	Result: FAILED
```
 All run logs are also saved so that comparison results can be examined. 

## tapout.sh
This is similar to tapout_sweep.py.
tapout.sh can be used to automatically run test with modified netlist, adding outputs to every operator in sorted order.

### Usage

First parameter is command that you are running. tapout.sh will modify netlist in this command and rerun it with new netlist file.
If there are n opertions, it can run test n times, or 1 time in case --single parameter is provided.
```build/bin/dbd_modify_netlist``` is required for tapout.sh to work. Run ``` make dbd ``` to build dbd_modify_netlist.

```
dbd/tapout.sh "./build/test/verif/op_tests/test_op --netlist verif/graph_tests/netlists/netlist_bert_mha.yaml --seed 0 --silicon --timeout 500"
dbd/tapout.sh "./build/test/verif/op_tests/test_op --netlist verif/graph_tests/netlists/netlist_bert_mha.yaml --seed 0 --silicon --timeout 500" --single
```
