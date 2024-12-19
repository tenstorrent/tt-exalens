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
0x00000000:  00001234  80380d10  31c07918  b66e0000
0x00000010:  01018020  00040000  80001000  c8000000
0x00000020:  02080000  a9000000  10191000  00212000
0x00000030:  080541c4  a94d0c80  fd74e115  01e0d3f4
```
Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8
```
Output:
```
18-18 (L1) : 0x00000000 (128 bytes)
0x00000000:  52   18   0    0    16   13   56  128  24   121  192  49   0    0    110  182
0x00000010:  32   128  1    1    0    0    4   0    0    16   0    128  0    0    0    200
0x00000020:  0    0    8    2    0    0    0   169  0    16   25   16   0    32   33   0
0x00000030:  196  65   5    8    128  12   77  169  21   225  116  253  244  211  224  1
0x00000040:  212  89   61   190  214  238  85  12   20   199  4    1    2    130  133  8
0x00000050:  213  33   132  80   2    145  0   93   14   106  193  144  197  41   101  154
0x00000060:  0    0    0    0    96   12   2   0    128  26   32   202  0    0    0    0
0x00000070:  112  10   0    80   90   130  45  72   187  9    108  219  24   111  98   146
```
Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 28027 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 28003 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 28042 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 28025 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 28040 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 28034 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 28088 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 27989 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 27980 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 28178 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  505410b9  55555555  55555555  55555555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  f7f581e7  b75555d7  e555f575  d4155575
0x00000030:  757555f5  555555d4  f45dee77  5575557f
```






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






## device / d

### Usage

```
device [<device-id> [<axis-coordinate> [<cell-contents>]]]
```


### Description

Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.


### Arguments

- `device-id`: ID of the device [default: 0]
- `axis-coordinate`: Coordinate system for the axis [default: netlist] Supported: netlist, noc0, noc1, nocTr, nocVirt, die, tensix
- `cell-contents`: A comma separated list of the cell contents [default: nocTr] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset) block - show the type of the block at that coordinate netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate


### Examples

Shows the status of the RISC-V for all devices
```
device
```
Output:
```
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
==== Device 1
    00    01    02    03    04    05    06    07
00  ----  ----  ----  ----  ----  ----  ----  ----
01  ----  ----  ----  ----  ----  ----  ----  ----
02  ----  ----  ----  ----  ----  ----  ----  ----
03  ----  ----  ----  ----  ----  ----  ----  ----
04  ----  ----  ----  ----  ----  ----  ----  ----
05  ----  ----  ----  ----  ----  ----  ----  ----
06  ----  ----  ----  ----  ----  ----  ----  ----
07  ----  ----  ----  ----  ----  ----  ----  ----
```
Shows noc0 to nocTr mapping for device 0
```
device 0 noc0
```
Output:
```
==== Device 0
11  dram  ----               ----               ----               ----               dram  ----               ----               ...
10  arc   ----               ----               ----               ----               dram  ----               ----               ...
09        harvested_workers  harvested_workers  harvested_workers  harvested_workers  dram  harvested_workers  harvested_workers  ...
08        harvested_workers  harvested_workers  harvested_workers  harvested_workers  dram  harvested_workers  harvested_workers  ...
07  dram  ----               ----               ----               ----               dram  ----               ----               ...
06  dram  eth                eth                eth                eth                dram  eth                eth                ...
05  dram  ----               ----               ----               ----               dram  ----               ----               ...
04        ----               ----               ----               ----               dram  ----               ----               ...
03  pcie  ----               ----               ----               ----               dram  ----               ----               ...
02        ----               ----               ----               ----               dram  ----               ----               ...
01  dram  ----               ----               ----               ----               dram  ----               ----               ...
00  dram  eth                eth                eth                eth                dram  eth                eth                ...
    00    01                 02                 03                 04                 05    06                 07                 ...
```
Shows netlist coordinates in noc0 coordinages for device 0
```
device 0 noc0 netlist
```
Output:
```
==== Device 0
11  N/A  7,0  7,1  7,2  7,3  N/A  7,4  7,5  7,6  7,7
10  N/A  6,0  6,1  6,2  6,3  N/A  6,4  6,5  6,6  6,7
09       N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A
08       N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A
07  N/A  5,0  5,1  5,2  5,3  N/A  5,4  5,5  5,6  5,7
06  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A
05  N/A  4,0  4,1  4,2  4,3  N/A  4,4  4,5  4,6  4,7
04       3,0  3,1  3,2  3,3  N/A  3,4  3,5  3,6  3,7
03  N/A  2,0  2,1  2,2  2,3  N/A  2,4  2,5  2,6  2,7
02       1,0  1,1  1,2  1,3  N/A  1,4  1,5  1,6  1,7
01  N/A  0,0  0,1  0,2  0,3  N/A  0,4  0,5  0,6  0,7
00  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A  N/A
    00   01   02   03   04   05   06   07   08   09
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
run-elf build/riscv-src/wormhole/sample.brisc.elf
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
