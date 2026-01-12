## burst-read-xy / brxy

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


### Examples

Read 1 word from address 0
```
brxy 0,0 0x0 1
```
Output:
```
1-1 (0,0) : 0x00000000 (4 total bytes)
(l1) : 0x00000000 (4 bytes)
0x00000000:  00001234
```
Read 16 words from address 0
```
brxy 0,0 0x0 16
```
Output:
```
1-1 (0,0) : 0x00000000 (64 total bytes)
(l1) : 0x00000000 (64 bytes)
0x00000000:  00001234  00001234  00001234  00001234
0x00000010:  00001234  00001234  00001234  00001234
0x00000020:  00001234  00001234  0062a023  ffb112b7
0x00000030:  00828293  00000313  00000393  40638333
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
1-1 (0,0) : 0x00000000 (128 total bytes)
(l1) : 0x00000000 (128 bytes)
0x00000000:  52   18   0    0  52   18   0   0  52   18   0    0    52   18   0    0
0x00000010:  52   18   0    0  52   18   0   0  52   18   0    0    52   18   0    0
0x00000020:  52   18   0    0  52   18   0   0  35   160  98   0    183  18   177  255
0x00000030:  147  130  130  0  19   3    0   0  147  3    0    0    51   131  99   64
0x00000040:  19   83   67   0  35   160  98  0  183  18   177  255  147  130  194  0
0x00000050:  19   3    16   0  35   160  98  0  183  18   177  255  147  130  2    1
0x00000060:  19   3    0    4  35   160  98  0  183  18   177  255  147  130  66   1
0x00000070:  19   3    128  0  147  3    16  0  3    174  2    0    3    174  2    0
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000000 (0) => 0x00001234 (4660) - 21803 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000004 (4) => 0x00001234 (4660) - 21814 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000008 (8) => 0x00001234 (4660) - 22006 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x0000000c (12) => 0x00001234 (4660) - 21904 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000010 (16) => 0x00001234 (4660) - 22126 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000014 (20) => 0x00001234 (4660) - 22077 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000018 (24) => 0x00001234 (4660) - 22092 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x0000001c (28) => 0x00001234 (4660) - 21679 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000020 (32) => 0x00001234 (4660) - 21889 times
Sampling for 0.15625 seconds...
1-1 (0,0) (l1) 0x00000024 (36) => 0x00001234 (4660) - 21995 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
0-0 (d0,0) : 0x00000000 (64 total bytes)
(dram_bank) : 0x00000000 (64 bytes)
0x00000000:  000000bb  55555555  55555555  55555555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  be5554d4  f455758f  75145554  f4d5d574
0x00000030:  5555f755  f5d55515  f55f5555  1cd55955
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.






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






## debug-bus / dbus

### Usage

```
debug-bus list-signals [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
debug-bus list-groups [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-groups>] [-s]
debug-bus group <group-name> <l1-address> [--samples <num>] [--sampling-interval <cycles>] [--search <pattern>] [--max <max-sigs>] [-d <device>] [-l <loc>] [-s]
debug-bus <signals> [-d <device>] [-l <loc>] [-s]
```


### Description

Commands for RISC-V debugging:
- list-signals:    List all predefined debug bus signal names.
--search:    Search for signals by pattern (wildcard format)
--max:       Limit number of results
- list-groups:   List all debug bus signal groups.
--search:    Search for groups by pattern (wildcard format)
--max:       Limit number of results
- group <group-name> <l1-address>:   List all signals in group using L1 sampling
--search:    Search for signals by pattern (wildcard format)
--samples:   Number of samples
--sampling-interval: Delay between samples
<l1-address>:      Byte address in L1 memory for L1 sampling mode (must be 16-byte aligned).
Enables L1 sampling: signal(s) are captured as 128-bit words to L1 memory at the given address
instead of direct 32-bit register read. Each sample uses 16 bytes. All samples must fit in the first 1 MiB (0x0 - 0xFFFFF).
- [<signals>]:   List of signals described by signal name or signal description.
<signal-description>: {DaisyId,RDSel,SigSel,Mask}
- DaisyId   - daisy chain identifier
- RDSel     - select 32bit data in 128bit register (values 0-3)
- SigSel    - select 128bit register
- Mask      - 32bit mask for significant bits (optional)


### Options

- `-s,` = **--simple**: Print simple output.
- `--search` = **\<pattern\>**: Search for signals by pattern (in wildcard format).
- `--max` = **\<max-sigs\>**: Limit --search output (default: 10, use --max "all" to print all matches). [default: 10].
- `--samples` = **\<num\>**: (L1 sampling only) Number of 128-bit samples to capture. [default: 1]
- `--sampling-interval` = **\<cycles\>**: (L1 sampling only, if --samples > 1) Delay in clock cycles between samples. Must be 2-256.[ default: 2]


### Examples

List up to 10 predefined debug bus signals (default max)
```
debug-bus list-signals
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0)
                                 Signals
╭──────────────────────────┬────────────────────────────────────┬───────╮
│ Group                    │ Name                               │ Value │
├──────────────────────────┼────────────────────────────────────┼───────┤
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_w_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_w_cr      │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_cr/0    │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_cr/1    │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_y_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_y_cr      │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_z_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_z_cr      │ 0x0   │
│ adcs0_unpacker0_channel1 │ adcs0_unpacker0_channel1_w_counter │ 0x0   │
╰──────────────────────────┴────────────────────────────────────┴───────╯

```
List all predefined debug bus signals
```
debug-bus list-signals --max all
```
Output:
```
=== Device 0 - location 0,0)
                                                     Signals
╭───────────────────────────────┬───────────────────────────────────────────────────────────────────┬────────────╮
│ Group                         │ Name                                                              │ Value      │
├───────────────────────────────┼───────────────────────────────────────────────────────────────────┼────────────┤
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_w_counter                                │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_w_cr                                     │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_x_counter                                │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_x_cr/0                                   │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_x_cr/1                                   │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_y_counter                                │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_y_cr                                     │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_z_counter                                │ 0x0        │
│ adcs0_unpacker0_channel0      │ adcs0_unpacker0_channel0_z_cr                                     │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_w_counter                                │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_w_cr                                     │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_x_counter                                │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_x_cr/0                                   │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_x_cr/1                                   │ 0x0        │
│ adcs0_unpacker0_channel1      │ adcs0_unpacker0_channel1_y_counter                                │ 0x0        │
...
```
List up to 5 signals whose names contain 'pc'
```
debug-bus list-signals --search *pc* --max 5
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0)
                        Signals
╭────────────────┬───────────────────────┬────────────╮
│ Group          │ Name                  │ Value      │
├────────────────┼───────────────────────┼────────────┤
│ brisc_group_a  │ brisc_dbg_obs_cmt_pc  │ 0x160      │
│ brisc_group_a  │ brisc_pc              │ 0x160      │
│ brisc_group_b  │ brisc_id_ex_pc        │ 0x160      │
│ ncrisc_group_a │ ncrisc_dbg_obs_cmt_pc │ 0x448a88   │
│ ncrisc_group_b │ ncrisc_id_ex_pc       │ 0x268898ac │
╰────────────────┴───────────────────────┴────────────╯

```
List all debug bus signal groups
```
debug-bus list-groups
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0 - Signal Groups ===
             Groups
╭───────────────────────────────╮
│ Group Name                    │
├───────────────────────────────┤
│ adcs0_unpacker0_channel0      │
│ adcs0_unpacker0_channel1      │
│ adcs0_unpacker1_channel0      │
│ adcs0_unpacker1_channel1      │
│ adcs2_packers_channel0        │
│ adcs2_packers_channel1        │
│ adcs_srca_srcb_access_control │
│ brisc_group_a                 │
│ brisc_group_b                 │
│ brisc_group_c                 │
╰───────────────────────────────╯

```
List groups whose names match pattern 'brisc'
```
debug-bus list-groups --search brisc*
```
Output:
```
=== Device 0 - location 0,0 - Signal Groups ===
     Groups
╭───────────────╮
│ Group Name    │
├───────────────┤
│ brisc_group_a │
│ brisc_group_b │
│ brisc_group_c │
╰───────────────╯

```
List all signals in group 'brisc_group_a' using L1 sampling, 4 samples, 10 cycles interval
```
debug-bus group brisc_group_a 0x1000 --samples 4 --sampling-interval 10
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a ===
                          brisc_group_a
╭────────────────────────┬──────────────────────────────────────╮
│ Name                   │ Value                                │
├────────────────────────┼──────────────────────────────────────┤
│ brisc_dbg_obs_cmt_pc   │ [0x160, 0x160, 0x160, 0x160]         │
│ brisc_dbg_obs_cmt_vld  │ [True, False, False, True]           │
│ brisc_dbg_obs_mem_addr │ [0x10000, 0x10000, 0x10000, 0x10000] │
│ brisc_dbg_obs_mem_rden │ [False, False, False, False]         │
│ brisc_i_instrn         │ [0x0, 0x6f, 0x0, 0x0]                │
│ brisc_i_instrn_req_rtr │ [True, True, True, True]             │
│ brisc_i_instrn_vld     │ [False, True, False, False]          │
│ brisc_o_instrn_addr    │ [0x160, 0x164, 0x164, 0x160]         │
│ brisc_o_instrn_req     │ [True, False, True, True]            │
│ brisc_pc               │ [0x160, 0x160, 0x160, 0x160]         │
╰────────────────────────┴──────────────────────────────────────╯

```
List all signals in group 'brisc_group_a' that ends with 'pc' using L1 sampling
```
debug-bus group brisc_group_a 0x1000 --search *pc
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a ===
         brisc_group_a
╭──────────────────────┬───────╮
│ Name                 │ Value │
├──────────────────────┼───────┤
│ brisc_dbg_obs_cmt_pc │ 0x160 │
│ brisc_pc             │ 0x160 │
╰──────────────────────┴───────╯

```
Print values for trisc0_pc and trisc1_pc
```
debug-bus trisc0_pc,trisc1_pc
```
Output:
```
device:0 loc:1-1 (0,0)  trisc0_pc: 0x6004
device:0 loc:1-1 (0,0)  trisc1_pc: 0xa004
```
Print value for a custom signal and trisc2_pc
```
debug-bus {7,0,12,0x3ffffff},trisc2_pc
```
Output:
```
device:0 loc:1-1 (0,0)  Daisy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff: 0x6004
device:0 loc:1-1 (0,0)  trisc2_pc: 0xe004
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## device / d

### Usage

```
device [-d <device-id>] [<axis-coordinate> [<cell-contents>]] [--no-legend]
```


### Description

Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.


### Options

- `-d` = **\<device-id\>**: ID of the device [default: all]
- `axis-coordinate`: Coordinate system for the axis [default: logical-tensix] Supported: noc0, noc1, translated, die, logical-tensix, logical-eth, logical-dram
- `cell-contents`: A comma separated list of the cell contents [default: riscv] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset), or block type if there are no RISC-V cores block - show the type of the block at that coordinate logical, noc0, noc1, translated, die - show coordinate noc0_id - show the NOC0 node ID (x-y) for the block noc1_id - show the NOC1 node ID (x-y) for the block


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

==== Device 0 [0x2618320aa]
    00     01     02     03     04     05     06     07
00  R----  -----  -----  -----  -----  -----  -----  -----
01  -----  -----  -----  -----  -----  -----  -----  -----
02  -----  -----  -----  -----  -----  -----  -----  -----
03  -----  -----  -----  -----  -----  -----  -----  -----
04  -----  -----  -----  -----  -----  -----  -----  -----
05  -----  -----  -----  -----  -----  -----  -----  -----
06  -----  -----  -----  -----  -----  -----  -----  -----
07  -----  -----  -----  -----  -----  -----  -----  -----
==== Device 1 [0x3618320aa]
    00     01     02     03     04     05     06     07
...
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
    harvested_eth
    arc
    dram
    harvested_dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0 [0x2618320aa]
    00           01     02     03     04     05    06     07     08     09
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

==== Device 0 [0x2618320aa]
    00    01    02    03    04    05    06    07
00  1-1   2-1   3-1   4-1   6-1   7-1   8-1   9-1
01  1-3   2-3   3-3   4-3   6-3   7-3   8-3   9-3
02  1-4   2-4   3-4   4-4   6-4   7-4   8-4   9-4
03  1-5   2-5   3-5   4-5   6-5   7-5   8-5   9-5
04  1-8   2-8   3-8   4-8   6-8   7-8   8-8   9-8
05  1-9   2-9   3-9   4-9   6-9   7-9   8-9   9-9
06  1-10  2-10  3-10  4-10  6-10  7-10  8-10  9-10
07  1-11  2-11  3-11  4-11  6-11  7-11  8-11  9-11
==== Device 1 [0x3618320aa]
    00    01    02    03    04    05    06    07
00  1-1   2-1   3-1   4-1   6-1   7-1   8-1   9-1
...
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend
```
Output:
```
==== Device 0 [0x2618320aa]
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
04  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
11  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
==== Device 1 [0x3618320aa]
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
...
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
    harvested_eth
    arc
    dram
    harvested_dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0 [0x2618320aa]
    00           01     02     03     04     05     06     07     08     09
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

==== Device 0 [0x2618320aa]
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
==== Device 0 [0x2618320aa]
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
04  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
11  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
```






## tensix

### Usage

```
dump-tensix-state [ <group> ] [ -d <device> ] [ -l <loc> ] [ -v ] [ -t <thread-id> ] [ -a <l1-address> ]
```


### Description

Prints the tensix state group of the given name, at the specified location and device.


### Options

- `group`: Tensix state group to dump. Options: [all, alu, pack, unpack, gpr, rwc, adc]
- `-t` = **\<thread-id\>**: Thread ID. Options: [0, 1, 2] Default: all (only for gpr group)
- `-a` = **\<l1-address\>**: L1 address to save group data. Only used for RWC and ADC groups.


### Examples

Prints tensix state for current device and core
```
tensix
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core using L1 address 0x0 for RWC and ADC groups
```
tensix -a 0x0
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for device with id 0 and current core
```
tensix -d 0
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core at location 0,0
```
tensix -l 0,0
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core
```
tensix all
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints alu configuration registers for current device and core
```
tensix alu
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
```
Prints packer's configuration registers for current device and core
```
tensix pack
```
Output:
```
Tensix registers for location 0,0 on device 0
PACKER
┌──────────────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ COUNTERS                 │ REG_ID = 1   │ REG_ID = 2   │ REG_ID = 3   │ REG_ID = 4   │
├──────────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ pack_per_xy_plane        │ 0            │ 0            │ 0            │ 0            │
│ pack_reads_per_xy_plane  │ 0            │ 0            │ 0            │ 0            │
│ pack_xys_per_til         │ 0            │ 0            │ 0            │ 0            │
│ pack_yz_transposed       │ False        │ False        │ False        │ False        │
│ pack_per_xy_plane_offset │ 0            │ 0            │ 0            │ 0            │
└──────────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
┌────────────────────────────────────┬──────────────────────────┬──────────────────────────┬──────────────────────────┬───────────...
│ PACK CONFIG                        │ REG_ID = 1               │ REG_ID = 2               │ REG_ID = 3               │ REG_ID = 4...
├────────────────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┼───────────...
│ row_ptr_section_size               │ 0                        │ 0                        │ 0                        │ 0         ...
│ exp_section_size                   │ 0                        │ 0                        │ 0                        │ 0         ...
│ l1_dest_addr                       │ 0x0                      │ 0x0                      │ 0x0                      │ 0x0       ...
│ uncompress                         │ False                    │ False                    │ False                    │ False     ...
│ add_l1_dest_addr_offset            │ False                    │ False                    │ False                    │ False     ...
│ reserved_0                         │ 0                        │ 0                        │ 0                        │ 0         ...
...
```
Prints unpacker's configuration registers for current device and core
```
tensix unpack
```
Output:
```
Tensix registers for location 0,0 on device 0
UNPACKER
┌─────────────────────────┬──────────────────────────┬──────────────────────────┐   ┌────────────────────┬────────────────────────...
│ UNPACK CONFIG           │ REG_ID = 1               │ REG_ID = 2               │   │ TILE DESCRIPTOR    │ REG_ID = 1             ...
├─────────────────────────┼──────────────────────────┼──────────────────────────┤   ├────────────────────┼────────────────────────...
│ out_data_format         │ TensixDataFormat.Float32 │ TensixDataFormat.Float32 │   │ in_data_format     │ TensixDataFormat.Float3...
│ throttle_mode           │ 0                        │ 0                        │   │ uncompressed       │ False                  ...
│ context_count           │ 0                        │ 0                        │   │ reserved_0         │ 0                      ...
│ haloize_mode            │ 0                        │ 0                        │   │ blobs_per_xy_plane │ 0                      ...
│ tileize_mode            │ 0                        │ 0                        │   │ reserved_1         │ 0                      ...
│ unpack_src_reg_set_upd  │ False                    │ False                    │   │ x_dim              │ 0                      ...
│ unpack_if_sel           │ False                    │ False                    │   │ y_dim              │ 0                      ...
│ upsample_rate           │ 0                        │ 0                        │   │ z_dim              │ 0                      ...
│ reserved_1              │ 0                        │ 0                        │   │ w_dim              │ 0                      ...
│ upsample_and_interleave │ False                    │ False                    │   │ blobs_y_start      │ 0                      ...
│ shift_amount            │ 0                        │ 0                        │   │ digest_type        │ 0                      ...
│ uncompress_cntx0_3      │ 0                        │ 0                        │   │ digest_size        │ 0                      ...
│ unpack_if_sel_cntx0_3   │ 0                        │ 0                        │   └────────────────────┴────────────────────────...
│ force_shared_exp        │ False                    │ False                    │                                                 ...
│ reserved_2              │ 0                        │ 0                        │                                                 ...
...
```
Prints general purpose registers for current device and core
```
tensix gpr
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐   ┌─────────────────────┬───────────...
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │   │ Thread 2            │ Values    ...
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤   ├─────────────────────┼───────────...
│ zero                        │ 1084818951      │   │ zero                     │ 589361604  │   │ zero                │ 9018386   ...
│ dbg_reserved                │ 398952542       │   │ dbg_reserved             │ 887226408  │   │ dbg_reserved        │ 1921018856...
│ dbg_msg                     │ 599523548       │   │ dbg_msg                  │ 3868280166 │   │ dbg_msg             │ 1029696891...
│ dbg_ckid                    │ 2589472545      │   │ dbg_ckid                 │ 2420130180 │   │ dbg_ckid            │ 168953440 ...
│ operand_base_addr           │ 0x7ea58540      │   │ perf_dbus_cntl           │ 3501338007 │   │ dest_offset_lo      │ 2692774472...
│ operand_offset_addr         │ 0x8f6207f6      │   │ perf_mem_dump_cntl_clear │ 518012928  │   │ gpr_5               │ 673437499 ...
│ gpr_6                       │ 839110649       │   │ perf_mem_dump_cntl_set   │ 1677891681 │   │ gpr_6               │ 3503253354...
│ gpr_7                       │ 2056486884      │   │ perf_cnt_start           │ 3898638422 │   │ gpr_7               │ 2014136456...
│ zero_0                      │ 641832192       │   │ perf_cnt_stop            │ 245170690  │   │ dest_offset_hi      │ 2604665604...
│ zero_1                      │ 2282723525      │   │ perf_epoch_base_addr     │ 0xf7bb3ae3 │   │ gpr_9               │ 205767679 ...
│ zero_2                      │ 2407422524      │   │ perf_epoch_offset        │ 8078434    │   │ gpr_10              │ 4252572127...
│ zero_3                      │ 4333776         │   │ gpr_11                   │ 12656940   │   │ gpr_11              │ 1150464916...
│ tmp0                        │ 366303285       │   │ gpr_12                   │ 2155889614 │   │ output_addr         │ 0x431052b7...
│ tmp1                        │ 2365010498      │   │ gpr_13                   │ 342009487  │   │ gpr_13              │ 636391995 ...
│ tile_size                   │ 2551574333      │   │ gpr_14                   │ 28655937   │   │ gpr_14              │ 703182562 ...
...
```
Prints all general purpose registers for current device and core
```
tensix gpr -v
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐   ┌─────────────────────┬───────────...
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │   │ Thread 2            │ Values    ...
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤   ├─────────────────────┼───────────...
│ zero                        │ 1084818951      │   │ zero                     │ 589361604  │   │ zero                │ 9018386   ...
│ dbg_reserved                │ 398952542       │   │ dbg_reserved             │ 887226408  │   │ dbg_reserved        │ 1921018856...
│ dbg_msg                     │ 599523548       │   │ dbg_msg                  │ 3868280166 │   │ dbg_msg             │ 1029696891...
│ dbg_ckid                    │ 2589472545      │   │ dbg_ckid                 │ 2420130180 │   │ dbg_ckid            │ 168953440 ...
│ operand_base_addr           │ 0x7ea58540      │   │ perf_dbus_cntl           │ 3501338007 │   │ dest_offset_lo      │ 2692774472...
│ operand_offset_addr         │ 0x8f6207f6      │   │ perf_mem_dump_cntl_clear │ 518012928  │   │ gpr_5               │ 673437499 ...
│ gpr_6                       │ 839110649       │   │ perf_mem_dump_cntl_set   │ 1677891681 │   │ gpr_6               │ 3503253354...
│ gpr_7                       │ 2056486884      │   │ perf_cnt_start           │ 3898638422 │   │ gpr_7               │ 2014136456...
│ zero_0                      │ 641832192       │   │ perf_cnt_stop            │ 245170690  │   │ dest_offset_hi      │ 2604665604...
│ zero_1                      │ 2282723525      │   │ perf_epoch_base_addr     │ 0xf7bb3ae3 │   │ gpr_9               │ 205767679 ...
│ zero_2                      │ 2407422524      │   │ perf_epoch_offset        │ 8078434    │   │ gpr_10              │ 4252572127...
│ zero_3                      │ 4333776         │   │ gpr_11                   │ 12656940   │   │ gpr_11              │ 1150464916...
│ tmp0                        │ 366303285       │   │ gpr_12                   │ 2155889614 │   │ output_addr         │ 0x431052b7...
│ tmp1                        │ 2365010498      │   │ gpr_13                   │ 342009487  │   │ gpr_13              │ 636391995 ...
│ tile_size                   │ 2551574333      │   │ gpr_14                   │ 28655937   │   │ gpr_14              │ 703182562 ...
...
```
Prints general purpose registers for threads 0 and 1 for current device and core
```
tensix gpr -t 0,1
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤
│ zero                        │ 1084818951      │   │ zero                     │ 589361604  │
│ dbg_reserved                │ 398952542       │   │ dbg_reserved             │ 887226408  │
│ dbg_msg                     │ 599523548       │   │ dbg_msg                  │ 3868280166 │
│ dbg_ckid                    │ 2589472545      │   │ dbg_ckid                 │ 2420130180 │
│ operand_base_addr           │ 0x7ea58540      │   │ perf_dbus_cntl           │ 3501338007 │
│ operand_offset_addr         │ 0x8f6207f6      │   │ perf_mem_dump_cntl_clear │ 518012928  │
│ gpr_6                       │ 839110649       │   │ perf_mem_dump_cntl_set   │ 1677891681 │
│ gpr_7                       │ 2056486884      │   │ perf_cnt_start           │ 3898638422 │
│ zero_0                      │ 641832192       │   │ perf_cnt_stop            │ 245170690  │
│ zero_1                      │ 2282723525      │   │ perf_epoch_base_addr     │ 0xf7bb3ae3 │
│ zero_2                      │ 2407422524      │   │ perf_epoch_offset        │ 8078434    │
│ zero_3                      │ 4333776         │   │ gpr_11                   │ 12656940   │
│ tmp0                        │ 366303285       │   │ gpr_12                   │ 2155889614 │
│ tmp1                        │ 2365010498      │   │ gpr_13                   │ 342009487  │
│ tile_size                   │ 2551574333      │   │ gpr_14                   │ 28655937   │
...
```
Prints RWC group for current device and core
```
tensix rwc
```
Output:
```
Tensix registers for location 0,0 on device 0
RWCs
┌──────────────────────────┬──────────┐   ┌─────────────────┬──────────┐   ┌─────────────────────┬──────────┐
│ CONTROL_SIGNALS          │ Values   │   │ COORDINATES_B   │ Values   │   │ FIDELITY_PHASE      │ Values   │
├──────────────────────────┼──────────┤   ├─────────────────┼──────────┤   ├─────────────────────┼──────────┤
│ i_thread_state_id        │ 0x0      │   │ rwc2_dst_cr     │ 0x0      │   │ rwc2_fidelity_phase │ 0x0      │
│ i_opcode[23..16]         │ 0x0      │   │ rwc2_dst        │ 0x0      │   │ rwc1_fidelity_phase │ 0x2      │
│ i_instrn_payload[54..48] │ 0x0      │   │ rwc1_dst_cr     │ 0x0      │   │ rwc0_fidelity_phase │ 0x2      │
│ i_instrn_payload[71..55] │ 0x0      │   │ rwc1_dst        │ 0x0      │   └─────────────────────┴──────────┘
│ i_opcode[15..8]          │ 0x0      │   └─────────────────┴──────────┘
│ i_instrn_payload[30..24] │ 0x0      │
│ i_instrn_payload[47..31] │ 0x0      │
│ i_opcode[8]              │ 0x0      │
│ i_instrn_payload[23..0]  │ 0x0      │
└──────────────────────────┴──────────┘
┌───────────────────────────────────────────────────────────────┬──────────┐   ┌─────────────────┬──────────┐
│ STATUS_SIGNALS                                                │ Values   │   │ COORDINATES_A   │ Values   │
├───────────────────────────────────────────────────────────────┼──────────┤   ├─────────────────┼──────────┤
│ (|math_winner_combo&math_instrn_pipe_ack)                     │ 0x0      │   │ rwc0_dst_cr     │ 0x0      │
│ debug_daisy_stop_issue0_debug_issue0_in0_math_instrn_pipe_ack │ 0x1      │   │ rwc0_dst        │ 0x0      │
...
```
Prints RWC group for current device and core using L1 address 0x0
```
tensix rwc -a 0x0
```
Output:
```
Tensix registers for location 0,0 on device 0
RWCs
┌──────────────────────────┬──────────┐   ┌─────────────────┬──────────┐   ┌─────────────────────┬──────────┐
│ CONTROL_SIGNALS          │ Values   │   │ COORDINATES_B   │ Values   │   │ FIDELITY_PHASE      │ Values   │
├──────────────────────────┼──────────┤   ├─────────────────┼──────────┤   ├─────────────────────┼──────────┤
│ i_thread_state_id        │ 0x0      │   │ rwc2_dst_cr     │ 0x0      │   │ rwc2_fidelity_phase │ 0x0      │
│ i_opcode[23..16]         │ 0x0      │   │ rwc2_dst        │ 0x0      │   │ rwc1_fidelity_phase │ 0x2      │
│ i_instrn_payload[54..48] │ 0x0      │   │ rwc1_dst_cr     │ 0x0      │   │ rwc0_fidelity_phase │ 0x2      │
│ i_instrn_payload[71..55] │ 0x0      │   │ rwc1_dst        │ 0x0      │   └─────────────────────┴──────────┘
│ i_opcode[15..8]          │ 0x0      │   └─────────────────┴──────────┘
│ i_instrn_payload[30..24] │ 0x0      │
│ i_instrn_payload[47..31] │ 0x0      │
│ i_opcode[8]              │ 0x0      │
│ i_instrn_payload[23..0]  │ 0x0      │
└──────────────────────────┴──────────┘
┌───────────────────────────────────────────────────────────────┬──────────┐   ┌─────────────────┬──────────┐
│ STATUS_SIGNALS                                                │ Values   │   │ COORDINATES_A   │ Values   │
├───────────────────────────────────────────────────────────────┼──────────┤   ├─────────────────┼──────────┤
│ (|math_winner_combo&math_instrn_pipe_ack)                     │ 0x0      │   │ rwc0_dst_cr     │ 0x0      │
│ debug_daisy_stop_issue0_debug_issue0_in0_math_instrn_pipe_ack │ 0x1      │   │ rwc0_dst        │ 0x0      │
...
```
Prints ADC group for current device and core
```
tensix adc
```
Output:
```
Tensix registers for location 0,0 on device 0
ADCs
No L1 address provided. Disabling atomic group reading for ADC group. Use -a option to specify L1 address.
┌────────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐
│ ADCS0_UNPACKER0_CHANNEL0   │ Values   │   │ ADCS2_PACKERS_CHANNEL1   │ Values   │   │ ADCS2_PACKERS_CHANNEL0   │ Values   │
├────────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤
│ w_cr                       │ 0x0      │   │ w_cr                     │ 0x0      │   │ w_cr                     │ 0x0      │
│ w_counter                  │ 0x0      │   │ w_counter                │ 0x0      │   │ w_counter                │ 0x0      │
│ z_cr                       │ 0x0      │   │ z_cr                     │ 0x0      │   │ z_cr                     │ 0x0      │
│ z_counter                  │ 0x0      │   │ z_counter                │ 0x0      │   │ z_counter                │ 0x0      │
│ y_cr                       │ 0x0      │   │ y_cr                     │ 0x0      │   │ y_cr                     │ 0x0      │
│ y_counter                  │ 0x0      │   │ y_counter                │ 0x0      │   │ y_counter                │ 0x0      │
│ x_cr                       │ 0x0      │   │ x_cr                     │ 0x0      │   │ x_cr                     │ 0x0      │
│ x_counter                  │ 0x0      │   │ x_counter                │ 0x0      │   │ x_counter                │ 0x0      │
└────────────────────────────┴──────────┘   └──────────────────────────┴──────────┘   └──────────────────────────┴──────────┘
┌────────────────────────────┬──────────┐   ┌────────────────────────────┬──────────┐   ┌────────────────────────────┬──────────┐
│ ADCS0_UNPACKER1_CHANNEL1   │ Values   │   │ ADCS0_UNPACKER1_CHANNEL0   │ Values   │   │ ADCS0_UNPACKER0_CHANNEL1   │ Values   │
├────────────────────────────┼──────────┤   ├────────────────────────────┼──────────┤   ├────────────────────────────┼──────────┤
│ w_cr                       │ 0x0      │   │ w_cr                       │ 0x0      │   │ w_cr                       │ 0x0      │
│ w_counter                  │ 0x0      │   │ w_counter                  │ 0x0      │   │ w_counter                  │ 0x0      │
...
```
Prints ADC group for current device and core using L1 address 0x0
```
tensix adc -a 0x0
```
Output:
```
Tensix registers for location 0,0 on device 0
ADCs
┌────────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐
│ ADCS0_UNPACKER0_CHANNEL0   │ Values   │   │ ADCS2_PACKERS_CHANNEL1   │ Values   │   │ ADCS2_PACKERS_CHANNEL0   │ Values   │
├────────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤
│ w_cr                       │ 0x0      │   │ w_cr                     │ 0x0      │   │ w_cr                     │ 0x0      │
│ w_counter                  │ 0x0      │   │ w_counter                │ 0x0      │   │ w_counter                │ 0x0      │
│ z_cr                       │ 0x0      │   │ z_cr                     │ 0x0      │   │ z_cr                     │ 0x0      │
│ z_counter                  │ 0x0      │   │ z_counter                │ 0x0      │   │ z_counter                │ 0x0      │
│ y_cr                       │ 0x0      │   │ y_cr                     │ 0x0      │   │ y_cr                     │ 0x0      │
│ y_counter                  │ 0x0      │   │ y_counter                │ 0x0      │   │ y_counter                │ 0x0      │
│ x_cr                       │ 0x0      │   │ x_cr                     │ 0x0      │   │ x_cr                     │ 0x0      │
│ x_counter                  │ 0x0      │   │ x_counter                │ 0x0      │   │ x_counter                │ 0x0      │
└────────────────────────────┴──────────┘   └──────────────────────────┴──────────┘   └──────────────────────────┴──────────┘
┌────────────────────────────┬──────────┐   ┌────────────────────────────┬──────────┐   ┌────────────────────────────┬──────────┐
│ ADCS0_UNPACKER1_CHANNEL1   │ Values   │   │ ADCS0_UNPACKER1_CHANNEL0   │ Values   │   │ ADCS0_UNPACKER0_CHANNEL1   │ Values   │
├────────────────────────────┼──────────┤   ├────────────────────────────┼──────────┤   ├────────────────────────────┼──────────┤
│ w_cr                       │ 0x0      │   │ w_cr                       │ 0x0      │   │ w_cr                       │ 0x0      │
│ w_counter                  │ 0x0      │   │ w_counter                  │ 0x0      │   │ w_counter                  │ 0x0      │
│ z_cr                       │ 0x0      │   │ z_cr                       │ 0x0      │   │ z_cr                       │ 0x0      │
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## dump-coverage / cov

### Usage

```
dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]
```


### Description

Get coverage data for a given ELF. Extract the gcda from the given core
and place it into the output directory along with its gcno.


### Arguments

- `elf`: Path to the currently running ELF
- `gcda_path`: Output path for the gcda
- `gcno_copy_path`: Optional path to copy the gcno file


### Examples

Pre-requisite: we have to run the elf before running coverage
```
re build/riscv-src/wormhole/cov_test.coverage.brisc.elf -r brisc
```
Command:
```
cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf cov_test.gcda cov_test.gcno
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## dump-gpr / gpr

### Usage

```
gpr [ <reg-list> ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]
```


### Description

Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
If the core cannot be halted, it prints nothing. If core is not active, an exception
is thrown.


### Options

- `reg-list`: List of registers to dump, comma-separated


### Examples

Command:
```
gpr
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register     brisc       trisc0    trisc1    trisc2    ncrisc
-----------  ----------  --------  --------  --------  --------
0 - zero     0x00000000
1 - ra       0x00000160
2 - sp       0xffb00ff0
3 - gp       0x00008800
4 - tp       0x00000000
5 - t0       0x00000001
6 - t1       0x00020000
7 - t2       0x00000008
8 - s0 / fp  0x00000000
9 - s1       0x00000000
10 - a0      0xffb00fcc
11 - a1      0x00000000
12 - a2      0x00000001
13 - a3      0x00000000
14 - a4      0x00000000
15 - a5      0x00000104
16 - a6      0x00000006
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    brisc       trisc0    trisc1    trisc2    ncrisc
----------  ----------  --------  --------  --------  --------
1 - ra      0x00000160
2 - sp      0xffb00ff0
32 - pc     0x00000160
Soft reset  False       True      True      True      True
Halted      False       -         -         -         -
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## gdb

### Usage

```
gdb start [<port>]
gdb stop
```


### Description

Starts or stops gdb server.


### Options

- `port`: Port of the GDB server. If not specified, an available port will be chosen.


### Examples

Command:
```
gdb start
```
Command:
```
gdb start 6767
```
Command:
```
gdb stop
```






## go

### Usage

```
go [-m <mode>] [-n <noc>] [ -d <device> ] [ -l <loc> ]
```


### Description

Sets the current device/location/noc/4B mode.


### Options

- `-m` = **\<mode\>**: Use 4B mode for communication with the device. [0: False, 1: True]
- `-n` = **\<noc\>**: Use NOC1 or NOC0 for communication with the device. [0: NOC0, 1: NOC1]


### Examples

Command:
```
go -m 1 -n 1 -d 0 -l 0,0
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## help / h

### Usage

```
help [--all] [-v] [<command>]
```


### Description

Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.


### Options

- `-v`: If specified, prints verbose documentation.
- `--all`: If specified, prints all commands.


### Examples

Command:
```
help exit
```
Output:
```
Full Name      Short    Description
-------------  -------  -----------------------------------------------------------------------------------
exit           x
                        Description:
                          Exits the program. The optional argument represents the exit code. Defaults to 0.
-------------  -------  -----------------------------------------------------------------------------------
```
Command:
```
help -v exit
```
Output:
```
Full Name      Short    Description
-------------  -------  -----------------------------------------------------------------------------------
exit           x
                        Description:
                          Exits the program. The optional argument represents the exit code. Defaults to 0.
-------------  -------  -----------------------------------------------------------------------------------
```
Command:
```
help --all
```
Output:
```
Full Name          Short    Description
-----------------  -------  ------------------------------------------------------------------------------------------------------...
exit               x        Exits the program. The optional argument represents the exit code. Defaults to 0.
reload             rl       Reloads files in cli_commands directory. Useful for development of commands.
help               h        Prints documentation summary. Use -v for details. If a command name is specified, it prints documentat...
burst-read-xy      brxy     Reads and prints a block of data from address 'addr' at core <core-loc>.
callstack          bt       Prints callstack using provided elf for a given RiscV core.
debug-bus          dbus     Commands for RISC-V debugging:
dump-tensix-state  tensix   Prints the tensix state group of the given name, at the specified location and device.
dump-gpr           gpr      Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
read               r        Reads and prints a block of data from address 'address'.
riscv              rv       Commands for RISC-V debugging:
tensix-reg         reg      Prints/writes to the specified register, at the specified location and device.
write-xy           wxy      Writes data word to address 'addr' at noc0 location x-y of the current chip.
device             d        Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.
dump-coverage      cov      Get coverage data for a given ELF. Extract the gcda from the given core
gdb                gdb      Starts or stops gdb server.
go                 go       Sets the current device/location/noc/4B mode.
noc                nc       Displays NOC (Network on Chip) registers.
run-elf            re       Loads an elf file into a brisc and runs it.
...
```






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

- `noc-id`: Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
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
│ write acks received        │ 0xffb20204 │ 0x00000000 │ │ write acks sent                │ 0xffb202c4 │ 0x001a96c5 │
│ read resps received        │ 0xffb20208 │ 0x00000000 │ │ read resps sent                │ 0xffb202c8 │ 0x00387443 │
│ read words received        │ 0xffb2020c │ 0x00000000 │ │ read words sent                │ 0xffb202cc │ 0x00387442 │
│ read reqs sent             │ 0xffb20214 │ 0x00000000 │ │ read reqs received             │ 0xffb202d4 │ 0x00387442 │
│ nonposted write words sent │ 0xffb20220 │ 0x00000000 │ │ nonposted write words received │ 0xffb202e0 │ 0x001a96c5 │
│ posted write words sent    │ 0xffb20224 │ 0x00000000 │ │ posted write words received    │ 0xffb202e4 │ 0x00000000 │
│ nonposted write reqs sent  │ 0xffb20228 │ 0x00000000 │ │ nonposted write reqs received  │ 0xffb202e8 │ 0x001a96c5 │
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
  read resps received          0xffb20208   0x00000000
  read words received          0xffb2020c   0x00000000
  read reqs sent               0xffb20214   0x00000000
  nonposted write words sent   0xffb20220   0x00000000
  posted write words sent      0xffb20224   0x00000000
  nonposted write reqs sent    0xffb20228   0x00000000
  posted write reqs sent       0xffb2022c   0x00000000


              Transaction Counters (Received)

  write acks sent                  0xffb202c4   0x001a96c5
  read resps sent                  0xffb202c8   0x00387463
  read words sent                  0xffb202cc   0x00387462
  read reqs received               0xffb202d4   0x00387462
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
│ NIU_MST_RD_REQ_SENT │ 0xffb20214 │ 0x00000000 │
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
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00000000 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x00000000 │
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
│ NIU_MST_RD_RESP_RECEIVED      │ 0xffb20208 │ 0x00000000 │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00000000 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x00000000 │
│ NIU_MST_RD_REQ_STARTED        │ 0xffb20238 │ 0x00000000 │
│ NIU_SLV_RD_RESP_SENT          │ 0xffb202c8 │ 0x00387480 │
│ NIU_SLV_RD_DATA_WORD_SENT     │ 0xffb202cc │ 0x0038747e │
│ NIU_SLV_RD_REQ_RECEIVED       │ 0xffb202d4 │ 0x00387480 │
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






## r

### Usage

```
read <address> [ <word-count> ] [ --format=hex8 ] [ --unsafe ] [ -r <risc_name> ] [ -d <device> ] [ -l <loc> ]
```


### Description

Reads and prints a block of data from address 'address'.


### Arguments

- `address`: Address to read from
- `word-count`: Number of words to read. [Default: 1]


### Options

- `--format` = **\<F\>**: Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex8]
- `-r` = **\<risc_name\>**: RISC core name if you want to read memory that is not exposed on NOC.
- `--unsafe`: Experts mode, allow reading everything (bypass safety checks).


### Examples

Read 1 word from address 0
```
read 0x0 1
```
Output:
```
Device 0 [0x2618320aa] | Location 1-1 (0,0) | Block l1 : 0x00000000 (1 bytes)
0x00000000:  93
```
Read 16 words from address 0
```
read 0x0 16
```
Output:
```
Device 0 [0x2618320aa] | Location 1-1 (0,0) | Block l1 : 0x00000000 (16 bytes)
0x00000000:  93  02  00  00  13  03  00  00  63  80  62  0a  b7  12  b1  ff
```
Prints 32 bytes in i8 format
```
read 0x0 32 --format i8
```
Output:
```
Device 0 [0x2618320aa] | Location 1-1 (0,0) | Block l1 : 0x00000000 (32 bytes)
0x00000000:  147  2  0  0  19  3   0   0  99  128  98  10  183  18  177  255
0x00000010:  19   3  0  0  19  83  67  0  35  160  98  0   183  18  177  255
```
Read 16 words from brisc private data memory
```
read 0xFFB0000 -r brisc 16
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
  HALTED PC=0x00000160 - brisc 0,0 [0]
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
Output:
```
Setting breakpoint at address 0 for brisc 0,0 [0]
Setting breakpoint at address 0 for trisc0 0,0 [0]
Setting breakpoint at address 0 for trisc1 0,0 [0]
Setting breakpoint at address 0 for trisc2 0,0 [0]
```
Delete breakpoint
```
riscv bkpt del 0
```
Output:
```
Deleting breakpoint 0 for brisc 0,0 [0]
Deleting breakpoint 0 for trisc0 0,0 [0]
Deleting breakpoint 0 for trisc1 0,0 [0]
Deleting breakpoint 0 for trisc2 0,0 [0]
```
Set a read watchpoint
```
riscv wchpt setr 0 0xc
```
Output:
```
Setting read watchpoint at address 0 for brisc 0,0 [0]
Setting read watchpoint at address 0 for trisc0 0,0 [0]
Setting read watchpoint at address 0 for trisc1 0,0 [0]
Setting read watchpoint at address 0 for trisc2 0,0 [0]
```
Set a write watchpoint
```
riscv wchpt setw 0 0xc
```
Output:
```
Setting write watchpoint at address 0 for brisc 0,0 [0]
Setting write watchpoint at address 0 for trisc0 0,0 [0]
Setting write watchpoint at address 0 for trisc1 0,0 [0]
Setting write watchpoint at address 0 for trisc2 0,0 [0]
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## run-elf / re

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






## server

### Usage

```
server start [--port <port>]
server stop
```


### Description

Starts or stops tt-exalens server.


### Examples

Command:
```
server start --port 5555
```
Output:
```
ttexalens-server listening on port 5555
```
Command:
```
server stop
```






## tensix-reg / reg

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
- `-n` = **\<noc-id\>**: NOC ID. Optional. Default: 0.


### Examples

Prints configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25)
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_a...
0
```
Prints debug register with address 0x54
```
reg dbg(0x54)
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
537329674
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
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_a...
TensixDataFormat.Float32
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
537329674
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18
```
Output:
```
Register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_address=None...
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0
```
Output:
```
Register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_address=No...
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## write-xy / wxy

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
