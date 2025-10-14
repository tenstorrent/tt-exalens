## brxy

### Usage

```
brxy <core-loc> <addr> [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <D>...]
```


### Description

Reads and prints a block of data from address 'addr' at core <core-loc>.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to read from
- `word-count`: Number of words to read. Default: 1


### Options

- `--sample` = **\<N\>**: Number of seconds to sample for. [default: 0] (single read)
- `--format` = **\<F\>**: Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
- `-o` = **\<O\>**: Address offset. Optional and repeatable.
- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Read 1 word from address 0
```
brxy 0,0 0x0 1
```
Output:
```
0,0 (L1) : 0x00000000 (4 bytes)
0x00000000:  00000168
```
Read 16 words from address 0
```
brxy 0,0 0x0 16
```
Output:
```
0,0 (L1) : 0x00000000 (64 bytes)
0x00000000:  00000168  00008010  80000190  00000000
0x00000010:  00000168  00008010  80000190  00000000
0x00000020:  00000168  00008010  80000190  00000000
0x00000030:  00000168  00008010  80000190  00000000
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
0,0 (L1) : 0x00000000 (128 bytes)
0x00000000:  104  1   0   0   16   128  0  0   144  1    0  128  0    0  0  0
0x00000010:  104  1   0   0   16   128  0  0   144  1    0  128  0    0  0  0
0x00000020:  104  1   0   0   16   128  0  0   144  1    0  128  0    0  0  0
0x00000030:  104  1   0   0   16   128  0  0   144  1    0  128  0    0  0  0
0x00000040:  104  1   0   0   16   128  0  0   144  1    0  128  0    0  0  0
0x00000050:  2    64  32  16  116  1    0  64  131  219  7  0    192  2  0  0
0x00000060:  2    64  32  16  116  1    0  64  131  219  7  0    192  2  0  0
0x00000070:  2    64  32  16  116  1    0  64  131  219  7  0    192  2  0  0
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000000 (0) => 0x00000168 (360) - 34273 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x00000168 (360) - 34011 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x00000168 (360) - 34300 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x00000168 (360) - 34258 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x00000168 (360) - 34679 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x00000168 (360) - 34351 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x00000168 (360) - 34952 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x00000168 (360) - 34587 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x00000168 (360) - 34599 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x00000168 (360) - 34005 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  000000bb  50000000  50540050  10500000
0x00000010:  40001050  50101410  00001000  00000400
0x00000020:  3f729a4e  3f7a8436  3eaa221c  3eeff550
0x00000030:  3f11e43a  3e2979a0  3e9ed1d4  3f3081cc
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## bt

### Usage

```
callstack <elf-files> [-o <offsets>] [-r <risc>] [-m <max-depth>] [-d <device>] [-l <loc>]
```


### Description

Prints callstack using provided elf for a given RiscV core.


### Arguments

- `<elf-files>`: Paths to the elf files to be used for callstack, comma separated.


### Options

- `-o` = **\<offsets\>**: List of offsets for each elf file, comma separated.
- `-r` = **\<risc\>**: RiscV name (e.g. brisc, triscs0, triscs1, triscs2, erisc). [default: first risc]
- `-m` = **\<max-depth\>**: Maximum depth of callstack. [Default: 100]


### Examples

Command:
```
callstack build/riscv-src/wormhole/sample.brisc.elf -r brisc
```
Output:
```
File build/riscv-src/wormhole/sample.brisc.elf does not exist
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## dbus

### Usage

```
debug-bus list-names [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
debug-bus list-groups [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--group <group-name>] [-s]
debug-bus [<signals>] [-v] [-d <device>] [-l <loc>] [--l1-address <addr> [--samples <num>] [--sampling-interval <cycles>]]
```


### Description

Commands for RISC-V debugging:
- list-names:    List all predefined debug bus signal names.
--search:
- list-groups:   List all debug bus signal groups or signals in a specific group.
--group:     Show signals in a specific group
--search:    Search for groups by pattern (in wildcard format)
- [<signals>]:   List of signals described by signal name or signal description.
<signal-description>: {DaisyId,RDSel,SigSel,Mask}
-DaisyId - daisy chain identifier
-RDSel   - select 32bit data in 128bit register -> values [0-3]
-SigSel  - select 128bit register
-Mask    - 32bit number to show only significant bits (optional)


### Options

- `-s,` = **--simple**: Print simple output.
- `--search` = **\<pattern\>**: Search for signals by pattern (in wildcard format).
- `--max` = **\<max-sigs\>**: Limit --search output (default: 10, use --max "all" to print all matches).
- `--group` = **\<group-names\>**: (list-groups only) List signals in the specified group(s). Multiple groups can be separated by commas.
- `--l1-address` = **\<addr\>**: Byte address in L1 memory for L1 sampling mode. Must be 16-byte aligned. When specified, enables L1 sampling mode which triggers a 128-bit capture of the signal into the core's L1 memory instead of a direct 32-bit register read. Each sample occupies 16 bytes (128 bits) in L1 memory. All samples must fit within the first 1 MiB of L1 memory (0x0 - 0xFFFFF).
- `--samples` = **\<num\>**: (L1-sampling mode only) Number of 128-bit samples to capture. [default: 1].
- `--sampling-interval` = **\<cycles\>**: (L1-sampling mode only) When samples > 1, this sets the delay in clock cycles between each sample. Must be between 2 and 256.


### Examples

List predefined debug bus signals
```
debug-bus list-names
```
Output:
```
=== Device 0 - location 0,0)
                                      Signals
╭─────────────────────────────────────────────────────────────────────┬────────────╮
│ Name                                                                │ Value      │
├─────────────────────────────────────────────────────────────────────┼────────────┤
│ brisc_pc                                                            │ 0x00000168 │
│ trisc0_pc                                                           │ 0x00005794 │
│ trisc1_pc                                                           │ 0x00005d70 │
│ trisc2_pc                                                           │ 0x00006378 │
│ ncrisc_pc                                                           │ 0x00004f98 │
│ brisc_ex_id_rtr                                                     │ 0x00000001 │
│ brisc_if_rts                                                        │ 0x00000001 │
│ brisc_if_ex_predicted                                               │ 0x00000000 │
│ brisc_if_ex_deco/1                                                  │ 0x00000000 │
│ brisc_if_ex_deco/0                                                  │ 0x0007db83 │
│ brisc_id_ex_rts                                                     │ 0x00000000 │
│ brisc_id_ex_pc                                                      │ 0x00000174 │
│ brisc_id_rf_wr_flag                                                 │ 0x00000001 │
│ brisc_id_rf_wraddr                                                  │ 0x00000002 │
│ brisc_id_rf_p1_rden                                                 │ 0x00000000 │
...
```
List up to 5 signals whose names contain pc
```
debug-bus list-names --search *pc* --max 5
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0)
         Signals
╭───────────┬────────────╮
│ Name      │ Value      │
├───────────┼────────────┤
│ brisc_pc  │ 0x00000168 │
│ trisc0_pc │ 0x00005794 │
│ trisc1_pc │ 0x00005d70 │
│ trisc2_pc │ 0x00006378 │
│ ncrisc_pc │ 0x00004f98 │
╰───────────┴────────────╯

```
List all debug bus signal groups
```
debug-bus list-groups
```
Output:
```
=== Device 0 - location 0,0 - Signal Groups ===
                  Groups
╭──────────────────────────┬──────────────╮
│ Group Name               │ Signal Count │
├──────────────────────────┼──────────────┤
│ brisc_group_a            │ 11           │
│ trisc0_group_a           │ 11           │
│ trisc1_group_a           │ 11           │
│ trisc2_group_a           │ 11           │
│ ncrisc_group_a           │ 11           │
│ brisc_group_b            │ 13           │
│ brisc_group_c            │ 12           │
│ trisc0_group_b           │ 13           │
│ trisc0_group_d           │ 21           │
│ trisc0_group_c           │ 13           │
│ trisc1_group_b           │ 13           │
│ trisc1_group_d           │ 23           │
│ trisc1_group_c           │ 12           │
│ trisc2_group_d           │ 23           │
│ trisc2_group_c           │ 12           │
...
```
List groups matching pattern
```
debug-bus list-groups --search *brisc*
```
Output:
```
=== Device 0 - location 0,0 - Signal Groups ===
             Groups
╭───────────────┬──────────────╮
│ Group Name    │ Signal Count │
├───────────────┼──────────────┤
│ brisc_group_a │ 11           │
│ brisc_group_b │ 13           │
│ brisc_group_c │ 12           │
╰───────────────┴──────────────╯

```
List all signals in brisc_group_a
```
debug-bus list-groups --group brisc_group_a
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a ===
                            Signals
╭─────────────────────────────────────────────────┬────────────╮
│ Name                                            │ Value      │
├─────────────────────────────────────────────────┼────────────┤
│ brisc_pc                                        │ 0x00000168 │
│ brisc_i_instrn_vld                              │ 0x00000000 │
│ brisc_i_instrn                                  │ 0x00000000 │
│ brisc_i_instrn_req_rtr                          │ 0x00000001 │
│ brisc_(o_instrn_req_early&~o_instrn_req_cancel) │ 0x00000000 │
│ brisc_o_instrn_addr                             │ 0x00000190 │
│ brisc_dbg_obs_mem_wren                          │ 0x00000000 │
│ brisc_dbg_obs_mem_rden                          │ 0x00000000 │
│ brisc_dbg_obs_mem_addr                          │ 0x00008010 │
│ brisc_dbg_obs_cmt_vld                           │ 0x00000000 │
│ brisc_dbg_obs_cmt_pc                            │ 0x00000168 │
╰─────────────────────────────────────────────────┴────────────╯

```
List signals from multiple groups
```
debug-bus list-groups --group brisc_group_a,trisc0_group_a,trisc1_group_a
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a (1/3) ===
                            Signals
╭─────────────────────────────────────────────────┬────────────╮
│ Name                                            │ Value      │
├─────────────────────────────────────────────────┼────────────┤
│ brisc_pc                                        │ 0x00000168 │
│ brisc_i_instrn_vld                              │ 0x00000000 │
│ brisc_i_instrn                                  │ 0x00000000 │
│ brisc_i_instrn_req_rtr                          │ 0x00000001 │
│ brisc_(o_instrn_req_early&~o_instrn_req_cancel) │ 0x00000000 │
│ brisc_o_instrn_addr                             │ 0x00000190 │
│ brisc_dbg_obs_mem_wren                          │ 0x00000000 │
│ brisc_dbg_obs_mem_rden                          │ 0x00000000 │
│ brisc_dbg_obs_mem_addr                          │ 0x00008010 │
│ brisc_dbg_obs_cmt_vld                           │ 0x00000000 │
│ brisc_dbg_obs_cmt_pc                            │ 0x00000168 │
╰─────────────────────────────────────────────────┴────────────╯


=== Device 0 - location 0,0 - Group: trisc0_group_a (2/3) ===
...
```
Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
```
debug-bus trisc0_pc,trisc1_pc
```
Output:
```
device:0 loc:1-1 (0,0)  trisc0_pc: 0x5794
device:0 loc:1-1 (0,0)  trisc1_pc: 0x5d70
```
Prints custom debug bus signal and trisc2_pc
```
debug-bus {7,0,12,0x3ffffff},trisc2_pc
```
Output:
```
device:0 loc:1-1 (0,0)  Debug Bus Config(Daisy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff) = 0x5794
device:0 loc:1-1 (0,0)  trisc2_pc: 0x6378
```
Read trisc0_pc using L1 sampling 5 times with 10 cycle interval
```
debug-bus trisc0_pc --l1-address 0x1000 --samples 5 --sampling-interval 10
```
Output:
```
device:0 loc:1-1 (0,0)  trisc0_pc [sample 0]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 1]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 2]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 3]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 4]: 0x5794
```
Read trisc0_pc using L1 sampling at address 0x2000
```
debug-bus trisc0_pc --l1-address 0x2000 --samples 3
```
Output:
```
device:0 loc:1-1 (0,0)  trisc0_pc [sample 0]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 1]: 0x5794
device:0 loc:1-1 (0,0)  trisc0_pc [sample 2]: 0x5794
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## device / d

### Usage

```
device [-d <device-id>] [<axis-coordinate> [<cell-contents>]] [--no-legend]
```


### Description

Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.


### Arguments

- `device-id`: ID of the device [default: all]
- `axis-coordinate`: Coordinate system for the axis [default: logical-tensix] Supported: noc0, noc1, translated, virtual, die, logical-tensix, logical-eth, logical-dram
- `cell-contents`: A comma separated list of the cell contents [default: riscv] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset), or block type if there are no RISC-V cores block - show the type of the block at that coordinate logical, noc0, noc1, translated, virtual, die - show coordinate noc0_id - show the NOC0 node ID (x-y) for the block noc1_id - show the NOC1 node ID (x-y) for the block


### Examples

Shows the status of the RISC-V for all devices
```
device
```
Output:
```

Legend:
  Axis coordinates: logical-tensix
  Cell contents: riscv
    riscv - show the status of the RISC-V ('R': running, '-': in reset)
  Colors:
    functional_workers

==== Device 0
    00     01     02     03     04     05     06     07
00  R----  -----  -----  -----  -----  -----  -----  -----
01  -----  -----  -----  -----  -----  -----  -----  -----
02  -----  -----  -----  -----  -----  -----  -----  -----
03  -----  -----  -----  -----  -----  -----  -----  -----
04  -----  -----  -----  -----  -----  -----  -----  -----
05  -----  -----  -----  -----  -----  -----  -----  -----
06  -----  -----  -----  -----  -----  -----  -----  -----
07  -----  -----  -----  -----  -----  -----  -----  -----
08  -----  -----  -----  -----  -----  -----  -----  -----
```
Shows the status of the RISC-V on noc0 axis for all devices
```
device noc0
```
Output:
```

Legend:
  Axis coordinates: noc0
  Cell contents: riscv
    riscv - show the status of the RISC-V ('R': running, '-': in reset)
  Colors:
    functional_workers
    eth
    arc
    dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0
    00           01     02     03     04     05    06     07     08     09
00  dram         R      R      R      R      dram  R      R      R      R
01  dram         R----  -----  -----  -----  dram  -----  -----  -----  -----
...
```
Shows noc0 coordinates on logical tensix axis for all devices
```
device logical-tensix noc0
```
Output:
```

Legend:
  Axis coordinates: logical-tensix
  Cell contents: noc0
  Colors:
    functional_workers

==== Device 0
    00    01    02    03    04    05    06    07
00  1-1   2-1   3-1   4-1   6-1   7-1   8-1   9-1
01  1-2   2-2   3-2   4-2   6-2   7-2   8-2   9-2
02  1-3   2-3   3-3   4-3   6-3   7-3   8-3   9-3
03  1-4   2-4   3-4   4-4   6-4   7-4   8-4   9-4
04  1-5   2-5   3-5   4-5   6-5   7-5   8-5   9-5
05  1-7   2-7   3-7   4-7   6-7   7-7   8-7   9-7
06  1-8   2-8   3-8   4-8   6-8   7-8   8-8   9-8
07  1-9   2-9   3-9   4-9   6-9   7-9   8-9   9-9
08  1-11  2-11  3-11  4-11  6-11  7-11  8-11  9-11
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend
```
Output:
```
==== Device 0
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
04  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
11  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
```
Shows the status of the RISC-V on die axis for device 0
```
device -d 0 die
```
Output:
```

Legend:
  Axis coordinates: die
  Cell contents: riscv
    riscv - show the status of the RISC-V ('R': running, '-': in reset)
  Colors:
    functional_workers
    eth
    arc
    dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0
    00           01     02     03     04     05     06     07     08     09
00  dram         R      R      R      R      R      R      R      R      dram
01  dram         -----  -----  -----  -----  -----  -----  -----  -----  dram
...
```
Shows noc0 coordinates on logical dram axis for device 0
```
device -d 0 logical-dram noc0
```
Output:
```

Legend:
  Axis coordinates: logical-dram
  Cell contents: noc0
  Colors:
    dram

==== Device 0
    00    01   02    03    04   05
00  0-0   0-5  5-0   5-2   5-3  5-5
01  0-1   0-6  5-1   5-9   5-4  5-6
02  0-11  0-7  5-11  5-10  5-8  5-7
```
Shows the block type on noc0 axis for device 0 without legend
```
device -d 0 noc0 block --no-legend
```
Output:
```
==== Device 0
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
04  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
11  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.






## cfg

### Usage

```
dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```


### Description

Prints the configuration register of the given name, at the specified location and device.


### Options

- `config-reg`: Configuration register name to dump. Options: [all, alu, pack, unpack] Default: all
- `-d` = **\<device\>**: Device ID. Optional. Default: current device
- `-l` = **\<loc\>**: Core location in X-Y or R,C format. Default: current core


### Examples

Prints all configuration registers for current device and core
```
cfg
```
Output:
```
Configuration registers for location 0,0 on device 0
ALU
┌───────────────────┬──────────────────────────┐
│ ALU CONFIG        │ VALUES                   │
├───────────────────┼──────────────────────────┤
│ Fpu_srnd_en       │ False                    │
│ Gasket_srnd_en    │ False                    │
│ Packer_srnd_en    │ False                    │
│ Padding           │ 0                        │
│ GS_LF             │ False                    │
│ Bfp8_HF           │ False                    │
│ SrcAUnsigned      │ False                    │
│ SrcBUnsigned      │ False                    │
│ Format_SrcA       │ TensixDataFormat.Float32 │
│ Format_SrcB       │ TensixDataFormat.Float32 │
│ Format_Dstacc     │ TensixDataFormat.Float32 │
│ Fp32_enabled      │ True                     │
│ SFPU_Fp32_enabled │ True                     │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints all configuration registers for device with id 0 and current core
```
cfg -d 0
```
Output:
```
Configuration registers for location 0,0 on device 0
ALU
┌───────────────────┬──────────────────────────┐
│ ALU CONFIG        │ VALUES                   │
├───────────────────┼──────────────────────────┤
│ Fpu_srnd_en       │ False                    │
│ Gasket_srnd_en    │ False                    │
│ Packer_srnd_en    │ False                    │
│ Padding           │ 0                        │
│ GS_LF             │ False                    │
│ Bfp8_HF           │ False                    │
│ SrcAUnsigned      │ False                    │
│ SrcBUnsigned      │ False                    │
│ Format_SrcA       │ TensixDataFormat.Float32 │
│ Format_SrcB       │ TensixDataFormat.Float32 │
│ Format_Dstacc     │ TensixDataFormat.Float32 │
│ Fp32_enabled      │ True                     │
│ SFPU_Fp32_enabled │ True                     │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Pirnts all configuration registers for current device and core at location 0,0
```
cfg -l 0,0
```
Output:
```
Configuration registers for location 0,0 on device 0
ALU
┌───────────────────┬──────────────────────────┐
│ ALU CONFIG        │ VALUES                   │
├───────────────────┼──────────────────────────┤
│ Fpu_srnd_en       │ False                    │
│ Gasket_srnd_en    │ False                    │
│ Packer_srnd_en    │ False                    │
│ Padding           │ 0                        │
│ GS_LF             │ False                    │
│ Bfp8_HF           │ False                    │
│ SrcAUnsigned      │ False                    │
│ SrcBUnsigned      │ False                    │
│ Format_SrcA       │ TensixDataFormat.Float32 │
│ Format_SrcB       │ TensixDataFormat.Float32 │
│ Format_Dstacc     │ TensixDataFormat.Float32 │
│ Fp32_enabled      │ True                     │
│ SFPU_Fp32_enabled │ True                     │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints all configuration registers for current device and core
```
cfg all
```
Output:
```
Configuration registers for location 0,0 on device 0
ALU
┌───────────────────┬──────────────────────────┐
│ ALU CONFIG        │ VALUES                   │
├───────────────────┼──────────────────────────┤
│ Fpu_srnd_en       │ False                    │
│ Gasket_srnd_en    │ False                    │
│ Packer_srnd_en    │ False                    │
│ Padding           │ 0                        │
│ GS_LF             │ False                    │
│ Bfp8_HF           │ False                    │
│ SrcAUnsigned      │ False                    │
│ SrcBUnsigned      │ False                    │
│ Format_SrcA       │ TensixDataFormat.Float32 │
│ Format_SrcB       │ TensixDataFormat.Float32 │
│ Format_Dstacc     │ TensixDataFormat.Float32 │
│ Fp32_enabled      │ True                     │
│ SFPU_Fp32_enabled │ True                     │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints alu configuration registers for current device and core
```
cfg alu
```
Output:
```
Configuration registers for location 0,0 on device 0
ALU
┌───────────────────┬──────────────────────────┐
│ ALU CONFIG        │ VALUES                   │
├───────────────────┼──────────────────────────┤
│ Fpu_srnd_en       │ False                    │
│ Gasket_srnd_en    │ False                    │
│ Packer_srnd_en    │ False                    │
│ Padding           │ 0                        │
│ GS_LF             │ False                    │
│ Bfp8_HF           │ False                    │
│ SrcAUnsigned      │ False                    │
│ SrcBUnsigned      │ False                    │
│ Format_SrcA       │ TensixDataFormat.Float32 │
│ Format_SrcB       │ TensixDataFormat.Float32 │
│ Format_Dstacc     │ TensixDataFormat.Float32 │
│ Fp32_enabled      │ True                     │
│ SFPU_Fp32_enabled │ True                     │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
```
Prints packer's configuration registers for current device and core
```
cfg pack
```
Output:
```
Configuration registers for location 0,0 on device 0
PACKER
┌──────────────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ COUNTERS                 │ REG_ID = 1   │ REG_ID = 2   │ REG_ID = 3   │ REG_ID = 4   │
├──────────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ pack_per_xy_plane        │ 0            │ 0            │ 0            │ 0            │
│ pack_reads_per_xy_plane  │ 16           │ 16           │ 16           │ 16           │
│ pack_xys_per_til         │ 0            │ 0            │ 0            │ 0            │
│ pack_yz_transposed       │ False        │ False        │ False        │ False        │
│ pack_per_xy_plane_offset │ 0            │ 0            │ 0            │ 0            │
└──────────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
┌────────────────────────────────────┬──────────────────────────┬──────────────────────────┬──────────────────────────┬───────────...
│ PACK CONFIG                        │ REG_ID = 1               │ REG_ID = 2               │ REG_ID = 3               │ REG_ID = 4...
├────────────────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┼───────────...
│ row_ptr_section_size               │ 0                        │ 0                        │ 0                        │ 0         ...
│ exp_section_size                   │ 4                        │ 4                        │ 4                        │ 4         ...
│ l1_dest_addr                       │ 0x80001cc3               │ 0x3f                     │ 0x7f                     │ 0xbf      ...
│ uncompress                         │ True                     │ True                     │ True                     │ True      ...
│ add_l1_dest_addr_offset            │ False                    │ False                    │ False                    │ False     ...
│ reserved_0                         │ 0                        │ 0                        │ 0                        │ 0         ...
...
```
Prints unpacker's configuration registers for current device and core
```
cfg unpack
```
Output:
```
Configuration registers for location 0,0 on device 0
UNPACKER
┌─────────────────────────┬──────────────────────────┬──────────────────────────┐   ┌────────────────────┬────────────────────────...
│ UNPACK CONFIG           │ REG_ID = 1               │ REG_ID = 2               │   │ TILE DESCRIPTOR    │ REG_ID = 1             ...
├─────────────────────────┼──────────────────────────┼──────────────────────────┤   ├────────────────────┼────────────────────────...
│ out_data_format         │ TensixDataFormat.Float32 │ TensixDataFormat.Float32 │   │ in_data_format     │ TensixDataFormat.Float3...
│ throttle_mode           │ 2                        │ 2                        │   │ uncompressed       │ True                   ...
│ context_count           │ 0                        │ 0                        │   │ reserved_0         │ 0                      ...
│ haloize_mode            │ 0                        │ 0                        │   │ blobs_per_xy_plane │ 0                      ...
│ tileize_mode            │ 0                        │ 0                        │   │ reserved_1         │ 0                      ...
│ unpack_src_reg_set_upd  │ False                    │ False                    │   │ x_dim              │ 0                      ...
│ unpack_if_sel           │ False                    │ False                    │   │ y_dim              │ 1                      ...
│ upsample_rate           │ 0                        │ 0                        │   │ z_dim              │ 4                      ...
│ reserved_1              │ 0                        │ 0                        │   │ w_dim              │ 0                      ...
│ upsample_and_interleave │ False                    │ False                    │   │ digest_type        │ 0                      ...
│ shift_amount            │ 0                        │ 0                        │   │ digest_size        │ 0                      ...
│ uncompress_cntx0_3      │ 15                       │ 15                       │   │ blobs_y_start      │ 0                      ...
│ unpack_if_sel_cntx0_3   │ 0                        │ 0                        │   └────────────────────┴────────────────────────...
│ force_shared_exp        │ False                    │ False                    │                                                 ...
│ reserved_2              │ 0                        │ 0                        │                                                 ...
...
```






## cov

### Usage

```
dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]
```


### Description

Get coverage data for a given ELF. Extract the gcda from the given core
and place it into the output directory along with its gcno.


### Arguments

- `device`: ID of the device [default: current active]
- `loc`: Location identifier (e.g. 0-0) [default: current active]
- `elf`: Path to the currently running ELF
- `gcda_path`: Output path for the gcda
- `gcno_copy_path`: Optional path to copy the gcno file


### Examples

Command:
```
cov build/riscv-src/wormhole/callstack.coverage.trisc0.elf coverage/callstack.gcda
```
Output:
```
dump-coverage: num_bytes must be greater than 0.
```
Command:
```
cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf coverage/cov_test.gcda coverage/cov_test.gcno
```
Output:
```
dump-coverage: num_bytes must be greater than 0.
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## gpr

### Usage

```
gpr [ <reg-list> ] [ <elf-file> ] [ -v ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]
```


### Description

Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
If the core cannot be halted, it prints nothing. If core is not active, an exception
is thrown.


### Options

- `reg-list`: List of registers to dump, comma-separated
- `elf-file`: Name of the elf file to use to resolve the source code location


### Examples

Command:
```
gpr
```
Command:
```
gpr ra,sp,pc
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## gdb

### Usage

```
gdb start --port <port>
gdb stop
```


### Description

Starts or stops gdb server.


### Examples

Command:
```
gdb start --port 6767
```
Command:
```
gdb stop
```






## go

### Usage

```
go [ -d <device> ] [ -l <loc> ]
```


### Description

Sets the current device/location.


### Examples

Command:
```
go -d 0 -l 0,0
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## noc / nc

### Usage

```
noc status [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
noc all [-d <device>] [-l <loc>] [-s]
noc register (<reg-names> | --search <reg-pattern> [--max <max-regs>]) [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
```


### Description

Displays NOC (Network on Chip) registers.
• "noc status" prints status registers for transaction counters.
• "noc all" prints all registers.
• "noc register <reg-names>" prints specific register(s) by name.
• "noc register --search <reg-pattern>" searches through all registers with the given wildcard pattern.


### Arguments

- `device-id`: ID of the device [default: current active]
- `noc-id`: Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
- `loc`: Location identifier (e.g. 0-0) [default: current active]
- `reg-names`: Name of specific NOC register(s) to display, can be comma-separated
- `reg-pattern`: Pattern in wildcard format for finding registers (mutually exclusive with <reg-names>)
- `max-regs`: Limit --search output (default: 10, use --max "all" to print all matches)


### Options

- `-s,` = **--simple**: Print simple output


### Examples

Prints status registers for device 0 on 0,0
```
noc status -d 0 -l 0,0
```
Output:
```
==== Device 0 - Location: 1-1
NOC0 Status Registers
              Transaction Counters (Sent)                              Transaction Counters (Received)
╭────────────────────────────┬────────────┬────────────╮ ╭────────────────────────────────┬────────────┬────────────╮
│ Name                       │ Address    │ Value      │ │ Name                           │ Address    │ Value      │
├────────────────────────────┼────────────┼────────────┤ ├────────────────────────────────┼────────────┼────────────┤
│ write acks received        │ 0xffb20204 │ 0x00000000 │ │ write acks sent                │ 0xffb202c4 │ 0x00041b7d │
│ read resps received        │ 0xffb20208 │ 0x000000c8 │ │ read resps sent                │ 0xffb202c8 │ 0x00292e0b │
│ read words received        │ 0xffb2020c │ 0x00006400 │ │ read words sent                │ 0xffb202cc │ 0x00292e0a │
│ read reqs sent             │ 0xffb20214 │ 0x000000c8 │ │ read reqs received             │ 0xffb202d4 │ 0x00292e0a │
│ nonposted write words sent │ 0xffb20220 │ 0x00000000 │ │ nonposted write words received │ 0xffb202e0 │ 0x0005701d │
│ posted write words sent    │ 0xffb20224 │ 0x00000000 │ │ posted write words received    │ 0xffb202e4 │ 0x00000000 │
│ nonposted write reqs sent  │ 0xffb20228 │ 0x00000000 │ │ nonposted write reqs received  │ 0xffb202e8 │ 0x00041b7d │
│ posted write reqs sent     │ 0xffb2022c │ 0x00000000 │ │ posted write reqs received     │ 0xffb202ec │ 0x00000000 │
╰────────────────────────────┴────────────┴────────────╯ ╰────────────────────────────────┴────────────┴────────────╯

NOC1 Status Registers
              Transaction Counters (Sent)                              Transaction Counters (Received)
╭────────────────────────────┬────────────┬────────────╮ ╭────────────────────────────────┬────────────┬────────────╮
│ Name                       │ Address    │ Value      │ │ Name                           │ Address    │ Value      │
...
```
Prints status registers with simple output
```
noc status -s
```
Output:
```
==== Device 0 - Location: 1-1
NOC0 Status Registers
              Transaction Counters (Sent)

  write acks received          0xffb20204   0x00000000
  read resps received          0xffb20208   0x000000c8
  read words received          0xffb2020c   0x00006400
  read reqs sent               0xffb20214   0x000000c8
  nonposted write words sent   0xffb20220   0x00000000
  posted write words sent      0xffb20224   0x00000000
  nonposted write reqs sent    0xffb20228   0x00000000
  posted write reqs sent       0xffb2022c   0x00000000


              Transaction Counters (Received)

  write acks sent                  0xffb202c4   0x00041b7d
  read resps sent                  0xffb202c8   0x00292e2b
  read words sent                  0xffb202cc   0x00292e2a
  read reqs received               0xffb202d4   0x00292e2a
...
```
Prints a specific register value
```
noc register NIU_MST_RD_REQ_SENT
```
Output:
```
==== Device 0 - Location: 1-1
                 NOC0 Registers
╭─────────────────────┬────────────┬────────────╮
│ Name                │ Address    │ Value      │
├─────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_REQ_SENT │ 0xffb20214 │ 0x000000c8 │
╰─────────────────────┴────────────┴────────────╯

                 NOC1 Registers
╭─────────────────────┬────────────┬────────────╮
│ Name                │ Address    │ Value      │
├─────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_REQ_SENT │ 0xffb30214 │ 0x00000000 │
╰─────────────────────┴────────────┴────────────╯

```
Prints multiple registers
```
noc register NIU_MST_RD_REQ_SENT,NIU_MST_RD_DATA_WORD_RECEIVED
```
Output:
```
==== Device 0 - Location: 1-1
                      NOC0 Registers
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00006400 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x000000c8 │
╰───────────────────────────────┴────────────┴────────────╯

                      NOC1 Registers
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb3020c │ 0x00000000 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb30214 │ 0x00000000 │
╰───────────────────────────────┴────────────┴────────────╯

```
Show all registers that have "_RD" in their name
```
noc register --search *_RD* --max all
```
Output:
```
==== Device 0 - Location: 1-1
                      NOC0 Registers
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0xffb20208 │ 0x000000c8 │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00006400 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x000000c8 │
│ NIU_MST_RD_REQ_STARTED        │ 0xffb20238 │ 0x000000c8 │
│ NIU_SLV_RD_RESP_SENT          │ 0xffb202c8 │ 0x00292e46 │
│ NIU_SLV_RD_DATA_WORD_SENT     │ 0xffb202cc │ 0x00292e47 │
│ NIU_SLV_RD_REQ_RECEIVED       │ 0xffb202d4 │ 0x00292e49 │
╰───────────────────────────────┴────────────┴────────────╯

                      NOC1 Registers
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0xffb30208 │ 0x00000000 │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb3020c │ 0x00000000 │
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## rv

### Usage

```
riscv (halt | step | cont | status) [-d <device>] [-r <risc>] [-l <loc>]
riscv rd [<address>] [-d <device>] [-r <risc>] [-l <loc>]
riscv rreg [<index>] [-d <device>] [-r <risc>] [-l <loc>]
riscv wr [<address>] [<data>] [-d <device>] [-r <risc>] [-l <loc>]
riscv wreg [<index>] [<data>] [-d <device>] [-r <risc>] [-l <loc>]
riscv bkpt (set | del) [<address>] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv wchpt (setr | setw | setrw | del) [<address>] [<data>] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv reset [1 | 0] [-d <device>] [-r <risc>] [-l <loc>]
```


### Description

Commands for RISC-V debugging:
- halt:    Stop the core and enter debug mode.
- step:    Execute one instruction and reenter debug mode.
- cont:    Exit debug mode and continue execution.
- status:  Print the status of the core.
- rd:      Read a word from memory.
- wr:      Write a word to memory.
- rreg:    Read a word from register.
- wreg:    Write a word to register.
- bkpt:    Set or delete a breakpoint. Address is required for setting.
- wchpt:   Set or delete a watchpoint. Address is required for setting.
- reset:   Sets (1) or clears (0) the reset signal for the core. If no argument is provided: set and clear.


### Options

- `-pt` = **\<point\>**: Index of the breakpoint or watchpoint register. 8 points are supported (0-7).


### Examples

Halt brisc
```
riscv halt
```
Print status
```
riscv status
```
Output:
```
  RUNNING - brisc 0,0 [0]
  IN RESET - trisc0 0,0 [0]
  IN RESET - trisc1 0,0 [0]
  IN RESET - trisc2 0,0 [0]
```
Step
```
riscv step
```
Continue
```
riscv cont
```
Write a word to address 0
```
riscv wr 0x0 0x2010006f
```
Read a word from address 0
```
riscv rd 0x0
```
Write a word to register 1
```
riscv wreg 1 0xabcd
```
Read a word from register 1
```
riscv rreg 1
```
Set breakpoint
```
riscv bkpt set 0 0x1244
```
Delete breakpoint
```
riscv bkpt del 0
```
Set a read watchpoint
```
riscv wchpt setr 0 0xc
```
Set a write watchpoint
```
riscv wchpt setw 0 0xc
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## re

### Usage

```
run-elf <elf-file> [ -v ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]
```


### Description

Loads an elf file into a brisc and runs it.


### Options

- `-r` = **\<risc\>**: RiscV name (brisc, triscs0, triscs1, triscs2, ncrisc, erisc). [default: first risc]


### Examples

Command:
```
run-elf build/riscv-src/wormhole/sample.brisc.elf
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## reg

### Usage

```
tensix-reg <register> [--type <data-type>] [ --write <value> ] [ -d <device> ] [ -l <loc> ] [-n <noc-id> ]
tensix-reg --search <register_pattern> [ --max <max-regs> ] [ -d <device> ] [ -l <loc> ] [-n <noc-id> ]
```


### Description

Prints/writes to the specified register, at the specified location and device.


### Arguments

- `<register>`: Register to dump/write to. Format: <reg-type>(<reg-parameters>) or register name.
- `<reg-type>`: Register type. Options: [cfg, dbg].
- `<reg-parameters>`: Register parameters, comma separated integers. For cfg: index,mask,shift. For dbg: address.
- `<register-pattern>`: Register pattern used to print register names that match it. Format: wildcard.


### Options

- `--type` = **\<data-type\>**: Data type of the register. This affects print format. Options: [INT_VALUE, ADDRESS, MASK, FLAGS, TENSIX_DATA_FORMAT]. Default: INT_VALUE.
- `--write` = **\<value\>**: Value to write to the register. If not given, register is dumped instead.
- `--max` = **\<max-regs\>**: Maximum number of register names to print when searching or all for everything. Default: 10.
- `-d` = **\<device\>**: Device ID. Optional. Default: current device.
- `-l` = **\<loc\>**: Core location in X-Y or R,C format. Default: current core.
- `-n` = **\<noc-id\>**: NOC ID. Optional. Default: 0.


### Examples

Prints configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25)
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, raw_ad...
0
```
Prints debug register with address 0x54
```
reg dbg(0x54)
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_addr...
0
```
Prints names of first 10 registers that start with PACK
```
reg --search PACK*
```
Output:
```
Register names that match pattern on device 0
PACK_CONFIG01_row_ptr_section_size
PACK_CONFIG01_exp_section_size
PACK_CONFIG01_l1_dest_addr
PACK_CONFIG01_uncompress
PACK_CONFIG01_add_l1_dest_addr_offset
PACK_CONFIG01_reserved_0
PACK_CONFIG01_out_data_format
PACK_CONFIG01_in_data_format
PACK_CONFIG01_reserved_1
PACK_CONFIG01_src_if_sel
Hit printing limit. To see more results, increase the --max value.
```
Prints names of first 5 registers that start with ALU
```
reg --search ALU* --max 5
```
Output:
```
Register names that match pattern on device 0
ALU_ROUNDING_MODE_Fpu_srnd_en
ALU_ROUNDING_MODE_Gasket_srnd_en
ALU_ROUNDING_MODE_Packer_srnd_en
ALU_ROUNDING_MODE_Padding
ALU_ROUNDING_MODE_GS_LF
Hit printing limit. To see more results, increase the --max value.
```
Prints names of all registers that include word format
```
reg --search *format* --max all
```
Output:
```
Register names that match pattern on device 0
UNPACK_TILE_DESCRIPTOR0_in_data_format
UNPACK_TILE_DESCRIPTOR1_in_data_format
UNPACK_CONFIG0_out_data_format
UNPACK_CONFIG1_out_data_format
ALU_FORMAT_SPEC_REG0_SrcAUnsigned
ALU_FORMAT_SPEC_REG0_SrcBUnsigned
ALU_FORMAT_SPEC_REG0_SrcA
ALU_FORMAT_SPEC_REG1_SrcB
ALU_FORMAT_SPEC_REG2_Dstacc
PACK_CONFIG01_out_data_format
PACK_CONFIG01_in_data_format
PACK_CONFIG08_out_data_format
PACK_CONFIG08_in_data_format
PACK_CONFIG11_out_data_format
PACK_CONFIG11_in_data_format
PACK_CONFIG18_out_data_format
PACK_CONFIG18_in_data_format
```
Prints register with name UNPACK_CONFIG0_out_data_format
```
reg UNPACK_CONFIG0_out_data_format
```
Output:
```
Value of register UNPACK_CONFIG0_out_data_format on device 0 and location 0,0:
TensixDataFormat.Float32
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, raw_ad...
TensixDataFormat.Float32
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_addr...
0
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18
```
Output:
```
Register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_address=None,...
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_addr...
18
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_addr...
18
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, raw_addr...
18
```






## wxy

### Usage

```
wxy <core-loc> <addr> <data> [--repeat <repeat>]
```


### Description

Writes data word to address 'addr' at noc0 location x-y of the current chip.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to write to
- `data`: Data to write


### Options

- `--repeat` = **\<repeat\>**: Number of times to repeat the write. Default: 1


### Examples

Command:
```
wxy 0,0 0x0 0x1234
```
Output:
```
0,0 (L1) : 0x00000000 (0) <= 0x00001234 (4660)
```
Command:
```
wxy 0,0 0x0 0x1234 --repeat 10
```
Output:
```
0,0 (L1) : 0x00000000 (0) <= 0x00001234 (4660)
0,0 (L1) : 0x00000004 (4) <= 0x00001234 (4660)
0,0 (L1) : 0x00000008 (8) <= 0x00001234 (4660)
0,0 (L1) : 0x0000000c (12) <= 0x00001234 (4660)
0,0 (L1) : 0x00000010 (16) <= 0x00001234 (4660)
0,0 (L1) : 0x00000014 (20) <= 0x00001234 (4660)
0,0 (L1) : 0x00000018 (24) <= 0x00001234 (4660)
0,0 (L1) : 0x0000001c (28) <= 0x00001234 (4660)
0,0 (L1) : 0x00000020 (32) <= 0x00001234 (4660)
0,0 (L1) : 0x00000024 (36) <= 0x00001234 (4660)
```
