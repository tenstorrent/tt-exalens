## jraxi

### Usage

```
jraxi <addr> [-d <D>...]
```


### Description

Reads data word from address 'addr' at AXI address of the current chip using jtag.


### Arguments

- `addr`: Address to read from


### Options

- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Command:
```
jraxi 0x0
```
Command:
```
jraxi 0xffb20110 -d 0
```






## jrxy

### Usage

```
jrxy <core-loc> <addr> [-d <D>...]
```


### Description

Reads data word from address 'addr' at noc0 location x-y of the current chip using jtag.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to read from


### Options

- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Command:
```
jrxy 18-18 0x0
```
Command:
```
jrxy 18-18 0x0 -d1
```






## jwaxi

### Usage

```
jwaxi <addr> <data> [-d <D>...]
```


### Description

Writes data word 'data' to address 'addr' at AXI address of the current chip using jtag.


### Arguments

- `addr`: Address to write to
- `data`: Data to write


### Options

- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Command:
```
jwaxi 0x0 0 -d1
```
Output:
```
device 1 (AXI) 0x00000000 (0) <= 0x00000000 (0)
```






## wxy

### Usage

```
wxy <core-loc> <addr> <data>
```


### Description

Writes data word to address 'addr' at noc0 location x-y of the current chip.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to read from
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






## device / d

### Usage

```
device [<device-id> [<axis-coordinate> [<cell-contents>]]]
```


### Description

Shows a device summary. When no argument is supplied, it iterates through all devices used by the
currently loaded netlist.


### Arguments

- `device-id`: ID of the device [default: 0]
- `axis-coordinate`: Coordinate system for the axis [default: netlist] Supported: netlist, noc0, noc1, nocTr, nocVirt, die, tensix
- `cell-contents`: A comma separated list of the cell contents [default: nocTr] Supported: op - show operation running on the core with epoch ID in parenthesis riscv - show the status of the RISC-V ('R': running, '-': in reset) block - show the type of the block at that coordinate netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate


### Examples

Shows op mapping for all devices
```
device
```
Output:
```
==== Device 0
    00    01    02    03    04    05    06    07
00  ----  R---  ----  ----  ----  ----  ----  ----
01  ----  ----  ----  ----  ----  ----  ----  ----
02  ----  ----  ----  ----  ----  ----  ----  ----
03  ----  ----  ----  ----  ----  ----  ----  ----
04  ----  ----  ----  ----  ----  ----  ----  ----
05  ----  ----  ----  ----  ----  ----  ----  ----
06  ----  ----  ----  ----  ----  ----  ----  ----
07  ----  ----  ----  ----  ----  ----  ----  ----
08  ----  ----  ----  ----  ----  ----  ----  ----
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
09        ----               ----               ----               ----               dram  ----               ----               ...
08        ----               ----               ----               ----               dram  ----               ----               ...
07  dram  ----               ----               ----               ----               dram  ----               ----               ...
06  dram  eth                eth                eth                eth                dram  eth                eth                ...
05  dram  ----               ----               ----               ----               dram  ----               ----               ...
04        ----               ----               ----               ----               dram  ----               ----               ...
03  pcie  harvested_workers  harvested_workers  harvested_workers  harvested_workers  dram  harvested_workers  harvested_workers  ...
02        ----               ----               ----               ----               dram  ----               ----               ...
01  dram  ----               R---               ----               ----               dram  ----               ----               ...
00  dram  eth                eth                eth                eth                dram  eth                eth                ...
    00    01                 02                 03                 04                 05    06                 07                 ...
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






## jwxy

### Usage

```
jwxy <core-loc> <addr> <data> [-d <D>...]
```


### Description

Writes data word 'data' to address 'addr' at noc0 location x-y of the current chip using jtag.


### Arguments

- `core-loc`: Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- `addr`: Address to write to
- `data`: Data to write


### Options

- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Command:
```
jwxy 18-18 0x0 0
```
Output:
```
device: 0 loc: 18-18 (L1) : 0x00000000 (0) <= 0x00000000 (0)
```
Command:
```
jwxy 18-18 0x0 0 -d1
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
0x00000000:  00001234  0000006f  00000013  00000013
0x00000010:  00000013  00010537  876545b7  00b52023
0x00000020:  0000006f  00052603  00030537  876545b7
0x00000030:  00b52023  00040537  00052603  0000006f
```
Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8
```
Output:
```
18-18 (L1) : 0x00000000 (128 bytes)
0x00000000:  52   18  0    0  111  0   0  0  19   0   0    0    19   0   0    0
0x00000010:  19   0   0    0  55   5   1  0  183  69  101  135  35   32  181  0
0x00000020:  111  0   0    0  3    38  5  0  55   5   3    0    183  69  101  135
0x00000030:  35   32  181  0  55   5   4  0  3    38  5    0    111  0   0    0
0x00000040:  19   0   0    0  19   0   0  0  19   0   0    0    19   0   0    0
0x00000050:  19   0   0    0  19   0   0  0  19   0   0    0    19   0   0    0
0x00000060:  19   0   0    0  19   0   0  0  19   0   0    0    19   0   0    0
0x00000070:  19   0   0    0  19   0   0  0  19   0   0    0    19   0   0    0
```
Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 28240 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 28420 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 28486 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 28510 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 28493 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 28627 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 28574 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 28667 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 28581 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 28632 times
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
0x00000020:  00000000  00000000  00000000  00000000
0x00000030:  00000000  00000000  00000000  00000000
```
