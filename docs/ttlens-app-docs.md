## wxy

### Usage

```
wxy <core-loc> <addr> <data>
```


### Description

Writes data word to address 'addr' at noc0 location x-y of the current chip.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to write to
- `data`: Data to write


### Examples

Command:
```
wxy 18-18 0x0 0x1234
```
Output:
```
18-18 (L1) : 0x00000000 (0) <= 0x00001234 (4660)
```






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






## re

### Usage

```
run-elf <elf-file> [ -v ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]
```


### Description

Loads an elf file into a brisc and runs it.


### Options

- `-r` = **\<risc\>**: RiscV ID (0: brisc, 1-3 triscs). [default: 0]


### Examples

Command:
```
run-elf build/risv-src/wormhole/sample.brisc.elf
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## rv

### Usage

```
riscv (halt | step | cont | status) [-v] [-d <device>] [-r <risc>] [-l <loc>]
riscv rd [<address>] [-v] [-d <device>] [-r <risc>] [-l <loc>]
riscv rreg [<index>] [-v] [-d <device>] [-r <risc>] [-l <loc>]
riscv wr [<address>] [<data>] [-v] [-d <device>] [-r <risc>] [-l <loc>]
riscv wreg [<index>] [<data>] [-v] [-d <device>] [-r <risc>] [-l <loc>]
riscv bkpt (set | del) [<address>] [-v] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv wchpt (setr | setw | setrw | del) [<address>] [<data>] [-v] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv reset [1 | 0] [-v] [-d <device>] [-r <risc>] [-l <loc>]
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
  IN RESET - BRISC 0,0 [0]
  IN RESET - TRISC0 0,0 [0]
  IN RESET - TRISC1 0,0 [0]
  IN RESET - TRISC2 0,0 [0]
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
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]
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
- `cell-contents`: A comma separated list of the cell contents [default: block] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset) block - show the type of the block at that coordinate logical, noc0, noc1, translated, virtual, die - show coordinate


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
    00    01    02    03    04    05    06    07
00  ----  ----  ----  ----  ----  ----  ----  ----
01  ----  ----  ----  ----  ----  ----  ----  ----
02  ----  ----  ----  ----  ----  ----  ----  ----
03  ----  ----  ----  ----  ----  ----  ----  ----
04  ----  ----  ----  ----  ----  ----  ----  ----
05  ----  ----  ----  ----  ----  ----  ----  ----
06  ----  ----  ----  ----  ----  ----  ----  ----
07  ----  ----  ----  ----  ----  ----  ----  ----
08  ----  ----  ----  ----  ----  ----  ----  ----
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

==== Device 0
    00    01    02    03    04    05    06    07    08    09
00  dram  eth   eth   eth   eth   dram  eth   eth   eth   eth
01  dram  ----  ----  ----  ----  dram  ----  ----  ----  ----
02        ----  ----  ----  ----  dram  ----  ----  ----  ----
03  pcie  ----  ----  ----  ----  dram  ----  ----  ----  ----
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
08  1-10  2-10  3-10  4-10  6-10  7-10  8-10  9-10
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend
```
Output:
```
==== Device 0
    00    01                  02                  03                  04                  05    06                  07            ...
00  dram  eth                 eth                 eth                 eth                 dram  eth                 eth           ...
01  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
02        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
03  pcie  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
04        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
05  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
06  dram  eth                 eth                 eth                 eth                 dram  eth                 eth           ...
07  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
08        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
09        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
10  arc   functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
11  dram  harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvested_work...
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

==== Device 0
    00    01    02    03    04    05    06    07    08    09
00  dram  eth   eth   eth   eth   eth   eth   eth   eth   dram
01  dram  ----  ----  ----  ----  ----  ----  ----  ----  dram
02  dram  ----  ----  ----  ----  ----  ----  ----  ----  dram
03  arc   ----  ----  ----  ----  ----  ----  ----  ----  dram
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
    00    01                  02                  03                  04                  05    06                  07            ...
00  dram  eth                 eth                 eth                 eth                 dram  eth                 eth           ...
01  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
02        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
03  pcie  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
04        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
05  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
06  dram  eth                 eth                 eth                 eth                 dram  eth                 eth           ...
07  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
08        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
09        functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
10  arc   functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
11  dram  harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvested_work...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.






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
Output:
```
RISC-V registers for location 0,0 on device 0
Register     BRISC    TRISC0    TRISC1    TRISC2
-----------  -------  --------  --------  --------
0 - zero
1 - ra
2 - sp
3 - gp
4 - tp
5 - t0
6 - t1
7 - t2
8 - s0 / fp
9 - s1
10 - a0
11 - a1
12 - a2
13 - a3
14 - a4
15 - a5
16 - a6
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    BRISC    TRISC0    TRISC1    TRISC2
----------  -------  --------  --------  --------
1 - ra
2 - sp
32 - pc
Soft reset  1        1         1         1
Halted      -        -         -         -
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]






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
brxy 18-18 0x0 1
```
Output:
```
18-18 (L1) : 0x00000000 (4 bytes)
0x00000000:  00001234
```
Read 16 words from address 0
```
brxy 18-18 0x0 16
```
Output:
```
18-18 (L1) : 0x00000000 (64 bytes)
0x00000000:  00001234  135a5719  560db495  2bbed9d7
0x00000010:  b2d386c9  18ea74c7  d08084aa  c800a290
0x00000020:  51528ef9  d8250037  c661fec2  ed5134e9
0x00000030:  132b0a06  a3202840  373a7ce4  4b0df440
```
Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8
```
Output:
```
18-18 (L1) : 0x00000000 (128 bytes)
0x00000000:  52   18   0    0    25   87   90   19   149  180  13   86   215  217  190  43
0x00000010:  201  134  211  178  199  116  234  24   170  132  128  208  144  162  0    200
0x00000020:  249  142  82   81   55   0    37   216  194  254  97   198  233  52   81   237
0x00000030:  6    10   43   19   64   40   32   163  228  124  58   55   64   244  13   75
0x00000040:  140  216  157  8    76   67   174  27   74   16   174  11   165  24   152  30
0x00000050:  32   4    193  56   5    202  68   216  68   249  8    169  131  100  46   3
0x00000060:  205  1    10   120  81   76   106  232  194  104  3    237  120  187  3    177
0x00000070:  44   224  17   12   65   174  132  44   28   164  228  106  207  45   219  22
```
Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 28998 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 28956 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 29020 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 29053 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 29146 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 29193 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 29155 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 29170 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 29128 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 29081 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  000000bb  55555555  55555555  55555555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  00010000  50044405  00444000  fd47eee5
0x00000030:  743d3170  00007f03  50400055  00000040
```
