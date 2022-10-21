# Debuda.py Demo

## Install graph-easy (optional)

Graph-Easy is a Perl-based program that renders .dot graphs in ASCII.
```
sudo apt install cpanminus
sudo cpanm Graph::Easy
```
Then add this alias to render the graph to Left->Right:
```
alias graph='sed '\''s/digraph G {/digraph G {\nrankdir=LR/g'\'' | graph-easy --as boxart 2>/dev/null'
```
Now, we can do something like this to render as simple graph
```
cat graph_test_op.netlist.dump | graph
```
You should see something like this:
```
     ┌────────┐  0   ┌───────┐  0   ┌─────────┐  0   ┌──────┐  0   ┌───────┐  0   ┌────────┐
     │ input0 │ ───▶ │ f_op0 │ ───▶ │ matmul1 │ ───▶ │ add1 │ ───▶ │ d_op3 │ ───▶ │ output │
     └────────┘      └───────┘      └─────────┘      └──────┘      └───────┘      └────────┘
                       │              ▲                ▲
  ┌────────────────────┘              │                │
  │                                   │                │
  │  ┌────────┐  0   ┌───────┐  1     │                │
  │  │ input1 │ ───▶ │ f_op1 │ ───────┘                │
  │  └────────┘      └───────┘                         │
  │                    │                               │
  │                    │ 0                             │
  │                    ▼                               │
  │                  ┌───────┐  1   ┌─────────┐  1     │
  │                  │ recip │ ───▶ │ matmul2 │ ───────┘
  │                  └───────┘      └─────────┘
  │   0                               ▲
  └───────────────────────────────────┘
  ```

## Compile test_op
```
make -j32 && make -j32 verif/op_tests/test_op
device/bin/silicon/reset.sh
./build/test/verif/op_tests/test_op --netlist dbd/test/netlists/netlist_multi_matmul_perf.yaml --seed 0 --silicon --timeout 500 && cat graph_test_op.netlist.dump | graph
```

Inset a a hang into the __recip__ node:
```
git apply dbd/test/inject-errors/sfpu_reciprocal-infinite-spin.patch
```

Rerun the test_op, and you should see a hang:
```
 Info    | IO               | get_tilizer cache MISS, added object to cache with tag 'input0'
 Info    | IO               | HW tilize input queue input0 push #0, host data_format=Float16, device data_format=Float16
 Info    | IO               | get_tilizer cache MISS, added object to cache with tag 'input1'
 Info    | IO               | HW tilize input queue input1 push #0, host data_format=Float16, device data_format=Float16
 Info    | Test             | Push Elapsed Time: 1275 us
 Info    | Runtime          | run_program for program program0
 Info    | Runtime          | run_execute_instrn graph = test_op, epoch_id = 0, input_count = 1, pc = 4
^C
```
Use ctrl-c to exit.

## Debugging

Start Debuda:
```
dbd/debuda.py
```
Debuda should detect the most recent subdirectory of tt_build as a default starting point. If you want a specific directory, supply `--netlist` argument and a 'positional' argument that points to the directory. For example:
```
dbd/debuda.py --netlist my-netlist.yaml tt-build/my-run-dir/
```

Show command docs: `help`
```
Short    Long                     Arguments            Description
-------  -----------------------  -------------------  ---------------------------------------------------------------------------------------------------------------
x        exit                                          exit the program
h        help                                          prints command documentation
e        epoch                    epoch_id             switch to epoch epoch_id
b        buffer                   buffer_id            prints details on the buffer with ID buffer_id
p        pipe                     pipe_id              prints details on the pipe with ID pipe_id
rxy      pci-read-xy              x y addr             read data from address 'addr' at noc0 location x-y of the chip associated with current epoch
brxy     burst-read-xy            x y addr burst_type  burst read data from address 'addr' at noc0 location x-y of the chip associated with current epoch.
                                                       NCRISC status code address=0xffb2010c, BRISC status code address=0xffb3010c
wxy      pci-write-xy             x y addr value       writes value to address 'addr' at noc0 location x-y of the chip associated with current epoch
dq       dram-queue                                    prints DRAM queue summary
hq       host-queue                                    prints Host queue summary
eq       epoch-queue                                   prints Epoch queue summary
fd       full-dump                                     performs a full dump at current x-y
test     test                                          test for development
srs      status-register-summary  verbosity [0-2]      prints brisc and ncrisc status registers.
abs      analyze-blocked-streams  verbosity [0-1]      reads stream information from the devices and highlights blocked streams (if verbosity is 1, print more detail)
t        dump-tile                tile_id, raw         prints tile for current stream in currently active phase. If raw=1, prints raw bytes
s        print-stream             x y stream_id        show stream 'stream_id' at core 'x-y'
om       op-map                                        draws a mini map of the current epoch
d        device-summary           device_id            shows summary of a device. When no argument is supplied, shows summary of all devices
c        core-summary             x y                  show summary for core 'x-y'
cdr      core-debug-regs          x y                  show debug registers for core 'x-y'. If coordinates are not supplied, show all cores.
```

Debuda will open a command prompt showing the currently selected epoch, core and stream. Some commands (such as stream-summary) will use the currently selected state to narrow down what to show.

## Top level view

Show cores with configured streams: `d`
```
Current epoch:0(test_op) device:0 core:3-3 rc:2,2 stream:8 > d
==== Device 0
09  .   .   .   .   .   .   .   .   .   .   .   .   Coordinate system: rc
08  .   .   .   .   .   .   .   .   .   .   .   .   Legend:
07  .   .   .   .   .   .   .   .   .   .   .   .   . - Functional worker
06  .   .   .   .   .   .   .   .   .   .   .   .   + - Functional worker with configured stream(s)
05  .   .   .   .   .   .   .   .   .   .   .   .
04  .   .   .   .   .   .   .   .   .   .   .   .
03  .   .   .   .   .   .   .   .   .   .   .   .
02  .   .   +   .   +   .   +   .   .   .   .   .
01  .   .   .   .   .   .   .   .   .   .   .   .
00  +   +   +   +   .   .   .   .   .   .   .   .
    00  01  02  03  04  05  06  07  08  09  10  11
```
Shows 'grid_loc' coordinates (elsewhere shown as `R,C`).
NOC0 coordinates are shown as `X-Y`.

Operation table can be shown with: `op-map`
```
Current epoch:0(test_op) device:0 core:3-3 rc:2,2 stream:8 > op-map
Op               Op type       Epoch    Device  Grid Loc    NOC0 Loc    Grid Size
---------------  ----------  -------  --------  ----------  ----------  -----------
test_op/f_op0    datacopy          0         0  [0, 0]      1-1         [1, 1]
test_op/matmul1  matmul            0         0  [0, 2]      3-1         [1, 1]
test_op/d_op3    datacopy          0         0  [0, 3]      4-1         [1, 1]
test_op/matmul2  matmul            0         0  [2, 4]      5-3         [1, 1]
test_op/recip    reciprocal        0         0  [2, 2]      3-3         [1, 1]
test_op/add1     add               0         0  [2, 6]      7-3         [1, 1]
test_op/f_op1    datacopy          0         0  [0, 1]      2-1         [1, 1]
```


## Examine DRAM queues
- Use `dram-queues` command to take a look at the DRAM queues: `dq`

```
Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > dq
DRAM queues for epoch 0
  Buffer ID  Op      Input Ops    Output Ops      dram_buf_flag    dram_io_flag    Channel  Address       RD ptr    WR ptr    Occupancy    Slots    Size [bytes]
-----------  ------  -----------  ------------  ---------------  --------------  ---------  ----------  --------  --------  -----------  -------  --------------
10000010000  output  d_op3                                    0               1          0  0x32000000         0         0            0        1          131072
10000050000  input0               f_op0                       1               0          0  0x30000000         0         1            1        1           66560
10000030000  input1               f_op1                       1               0          0  0x31000000         0         1            1        1           66560
```

## Analyze blocked streams

- Condensed version: `abs`
```
Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > abs
Analyzing device 1/1
Loading device.read_all_stream_registers () cache from file device0-stream-cache.pkl
X-Y    Op                          Stream  Type      Epoch    Phase    MSGS_REMAINING    MSGS_RECEIVED  Depends on    State    Flag
-----  ------------------------  --------  ------  -------  -------  ----------------  ---------------  ------------  -------  ------
3-3    test_op/recip:reciprocal         8  input         0        1                32                2  2-1           Active   All core inputs ready, but no output generated
Speed dial:
  #  Description    Command
---  -------------  ---------
  0  Go to stream   s 3 3 8
  ```

- Detailed version: `abs 1`

```
X-Y    Op                          Stream  Type            Epoch    Phase    MSGS_REMAINING    MSGS_RECEIVED  Depends on       State    Flag
-----  ------------------------  --------  ------------  -------  -------  ----------------  ---------------  ---------------  -------  ------
2-1    test_op/f_op1:datacopy           8  input               0        1                 0                0  2-1
                                       24  output              0        1                 0                0
                                       40  op-relay            0        1                 0                0
                                       41  op-relay            0        1                24                2                   Active
3-1    test_op/matmul1:matmul           8  input               0        1                 0                0  2-1
                                        9  input               0        1                 0                0
                                       24  output              0        1                56                2                   Active
                                       32  intermediate        0        1                64                0
3-3    test_op/recip:reciprocal         8  input               0        1                32                2  2-1              Active   All core inputs ready, but no output generated
                                       24  output              0        1                32                0
5-3    test_op/matmul2:matmul           8  input               0        1                32                2  2-1 3-3          Active
                                        9  input               0        1                32                0
                                       24  output              0        1                64                0
                                       32  intermediate        0        1                64                0
7-3    test_op/add1:add                 8  input               0        1                64                2  2-1 5-3 3-1 3-3  Active
                                        9  input               0        1                64                0
                                       24  output              0        1                64                0
Speed dial:
  #  Description    Command
---  -------------  ---------
  0  Go to stream   s 2 1 41
  1  Go to stream   s 3 1 24
  2  Go to stream   s 3 3 8
  3  Go to stream   s 5 3 8
  4  Go to stream   s 7 3 8
  ```

- Navigate to stream 3-3-8 by using speed-dial: `3`
```
Current epoch:0(test_op) device:0 core:2-1 rc:0,1 stream:41 > 3
Non-idle streams                       Registers                                                     Stream (blob.yaml)                        Buffer 10000200000                          Pipe 10000320000
------------------  -----------------  ------------------------------------------------  ----------  ---------------------------  -----------  -----------------------------  -----------  ------------------  -------------
8                   RS-10(2)-10(1)-41  STREAM_ID                                         8           buf_addr                     196608       md_op_name                     recip        id                  10000320000
24                  RR-5-3-9           PHASE_AUTO_CFG_PTR (word addr)                    0x18394     buf_id                       10000200000  id                             0            input_list          [10000130000]
                                       CURR_PHASE                                        1           buf_size                     16640        uniqid                         10000200000  output_list         [10000200000]
                                       CURR_PHASE_NUM_MSGS_REMAINING                     32          buf_space_available_ack_thr  0            epoch_tiles                    32           outgoing_noc_id     0
                                       NUM_MSGS_RECEIVED                                 2           data_auto_send               True         chip_id                        [0]          mcast_core_rc       [0, 0, 1]
                                       NEXT_MSG_ADDR                                     0x3000      dest                         []           core_coordinates               (2, 2)
                                       NEXT_MSG_SIZE                                     0x82        fork_stream_ids              []           size_tiles                     8
                                       OUTGOING_DATA_NOC                                 0           input_index                  0            scatter_gather_num_tiles       32
                                       LOCAL_SOURCES_CONNECTED                           0           intermediate                 False        is_scatter                     0
                                       SOURCE_ENDPOINT                                   0           msg_info_buf_addr            0            replicate                      0
...
...
```

- Show NCRISC/BRISC registers `srs 0`:
```
Current epoch:0(test_op) device:0 core:3-3 rc:2,2 stream:8 > srs 0
Reading status registers on device 0...
NCRISC status summary:
X-Y    Status    Status Description
-----  --------  ---------------------------
2-1    11111111  Main loop begin
3-1    11111111  Main loop begin
3-3    11111111  Main loop begin
4-1    f2000000  Ready to write data to dram
5-3    11111111  Main loop begin
7-3    11111111  Main loop begin
BRISC status summary:
X-Y    Status    Status Description
-----  --------  ------------------------------------------------------
2-1    b0000018  Stream restart check
3-1    b0000008  Stream restart check
3-3    e0000000  Check and push pack stream that has data (TM ops only)
4-1    e0000000  Check and push pack stream that has data (TM ops only)
5-3    e0000000  Check and push pack stream that has data (TM ops only)
7-3    e0000000  Check and push pack stream that has data (TM ops only)
```
Since this is live data, rerunning the command can show different statuses.

Use `srs 1` and `srs 2` for more verbose output.

Show core debug registers: `cdr 3 3`

```
Current epoch:0(test_op) device:0 core:3-3 rc:2,2 stream:8 > cdr 3 3
=== Debug registers for core 3-3 ===
T0               T1               T2               FW
-------  ------  -------  ------  -------  ------  -------  ------
DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000
DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000
DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000
DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000
DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000
DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000
DBG[6]   0x0000  DBG[6]   0x0000  DBG[6]   0x0000  DBG[6]   0x0000
...
```


## Scripting

### Simple scripting with --commands argument

When debuda encounters `--command` argument it will treat it as a semicolon-separated list of commands to run.
If the last command is `exit`, Debuda will terminate. For example:
```
dbd/debuda.py --commands "cdr 3 3; exit"
```


### Commands/ folder

A python file placed into commands/ folder becomes a command available to Debuda.

Define some metadata for the command first:
```c++
from tabulate import tabulate

command_metadata = {
        "short" : "om",
        "expected_argument_count" : [ 0 ],
        "arguments" : "",
        "description" : "Draws a mini map of the current epoch"
    }
```
Then define function run(). This example shows the `op-map` command:
```python
def run(args, context, ui_state = None):
    navigation_suggestions = []

    rows = []
    for graph_name, graph in context.netlist.graphs.items():
        epoch_id = context.netlist.graph_name_to_epoch_id (graph_name)
        device_id = context.netlist.graph_name_to_device_id (graph_name)
        device = context.devices[device_id]
        for op_name in graph.op_names():
            op = graph.root[op_name]
            grid_loc = op['grid_loc']
            noc0_x, noc0_y = device.rc_to_noc0 (grid_loc[0], grid_loc[1])
            row = [ f"{graph_name}/{op_name}", op['type'], epoch_id, f"{graph.root['target_device']}", f"{grid_loc}", f"{noc0_x}-{noc0_y}", f"{op['grid_size']}"]
            rows.append (row)

    print (tabulate(rows, headers = [ "Op", "Op type", "Epoch", "Device", "Grid Loc", "NOC0 Loc", "Grid Size" ]))

    return navigation_suggestions
```