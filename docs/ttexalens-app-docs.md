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
  HALTED PC=0x00000c4c - BRISC 0,0 [0]
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
0x00000000:  2010006f
```
Read 16 words from address 0
```
brxy 0,0 0x0 16
```
Output:
```
0,0 (L1) : 0x00000000 (64 bytes)
0x00000000:  2010006f  0000006f  00000013  00000013
0x00000010:  00000013  00010537  876545b7  00b52023
0x00000020:  0000006f  00052603  00030537  876545b7
0x00000030:  00b52023  00040537  00052603  0000006f
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
0,0 (L1) : 0x00000000 (128 bytes)
0x00000000:  111  0   16   32  111  0   0  0  19   0   0    0    19   0   0    0
0x00000010:  19   0   0    0   55   5   1  0  183  69  101  135  35   32  181  0
0x00000020:  111  0   0    0   3    38  5  0  55   5   3    0    183  69  101  135
0x00000030:  35   32  181  0   55   5   4  0  3    38  5    0    111  0   0    0
0x00000040:  19   0   0    0   19   0   0  0  19   0   0    0    19   0   0    0
0x00000050:  19   0   0    0   19   0   0  0  19   0   0    0    19   0   0    0
0x00000060:  19   0   0    0   19   0   0  0  19   0   0    0    19   0   0    0
0x00000070:  19   0   0    0   19   0   0  0  19   0   0    0    19   0   0    0
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000000 (0) => 0x2010006f (537919599) - 25994 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x2010006f (537919599) - 25959 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x2010006f (537919599) - 25972 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x2010006f (537919599) - 26021 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x2010006f (537919599) - 25968 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x2010006f (537919599) - 25992 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x2010006f (537919599) - 26008 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x2010006f (537919599) - 26014 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x2010006f (537919599) - 26018 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x2010006f (537919599) - 26029 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  000000bb  00000000  00000000  00000000
0x00000010:  00000000  00000000  00000000  00000000
0x00000020:  00000000  00000000  00000000  00000000
0x00000030:  00000000  00000000  00000000  00000000
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
    00    01    02    03    04    05    06    07    08    09    10    11
00  R---  R---  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
01  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
02  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
03  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
04  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
05  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
06  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
07  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
08  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
09  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
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
    00    01    02    03    04    05    06    07    08    09    10    11    12
00        dram              dram              dram              dram
01        R---  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
02  arc   R---  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
03        ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
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
    00     01     02     03     04    05    06    07    08    09    10     11
00  1-1    1-2    1-3    1-4    1-5   1-7   1-8   1-9   1-10  1-11  2-1    2-2
01  2-3    2-4    2-5    2-7    2-8   2-9   2-10  2-11  3-1   3-2   3-3    3-4
02  3-5    3-7    3-8    3-9    3-10  3-11  4-1   4-2   4-3   4-4   4-5    4-7
03  4-8    4-9    4-10   4-11   5-1   5-2   5-3   5-4   5-5   5-7   5-8    5-9
04  5-10   5-11   6-1    6-2    6-3   6-4   6-5   6-7   6-8   6-9   6-10   6-11
05  7-1    7-2    7-3    7-4    7-5   7-7   7-8   7-9   7-10  7-11  8-1    8-2
06  8-3    8-4    8-5    8-7    8-8   8-9   8-10  8-11  9-1   9-2   9-3    9-4
07  9-5    9-7    9-8    9-9    9-10  9-11  10-1  10-2  10-3  10-4  10-5   10-7
08  10-8   10-9   10-10  10-11  11-1  11-2  11-3  11-4  11-5  11-7  11-8   11-9
09  11-10  11-11  12-1   12-2   12-3  12-4  12-5  12-7  12-8  12-9  12-10  12-11
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend
```
Output:
```
==== Device 0
    00    01                  02                  03                  04                  05                  06                  ...
00        dram                                                        dram                                                        ...
01        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
02  arc   functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
03        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
04  pcie  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
05        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
06        dram                                                        dram                                                        ...
07        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
08        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
09        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
10        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
11        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
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
    00    01    02    03    04    05    06    07    08    09    10    11    12
00              dram              dram              dram              dram
01        ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
02        ----  R---  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
03        ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----  ----
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
    00   01   02   03   04   05   06    07
00  1-0  1-6  4-0  4-6  7-0  7-6  10-0  10-6
```
Shows the block type on noc0 axis for device 0 without legend
```
device -d 0 noc0 block --no-legend
```
Output:
```
==== Device 0
    00    01                  02                  03                  04                  05                  06                  ...
00        dram                                                        dram                                                        ...
01        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
02  arc   functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
03        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
04  pcie  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
05        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
06        dram                                                        dram                                                        ...
07        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
08        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
09        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
10        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
11        functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.






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
wxy 0,0 0x0 0x1234
```
Output:
```
0,0 (L1) : 0x00000000 (0) <= 0x00001234 (4660)
```






## bt

### Usage

```
callstack <elf-file> [-r <risc>] [-m <max-depth>] [-v] [-d <device>] [-l <loc>]
```


### Description

Prints callstack using provided elf for a given RiscV core.


### Options

- `-r` = **\<risc\>**: RiscV ID (0: brisc, 1-3 triscs). [Default: 0]
- `-m` = **\<max-depth\>**: Maximum depth of callstack. [Default: 100]


### Examples

Command:
```
callstack build/riscv-src/wormhole/sample.brisc.elf -r 0
```
Output:
```
Location: 1-1 (0,0), core: BRISC
  #0 0x00000C40 in main () at /localdev/macimovic/work/tt-exalens/ttexalens/riscv-src/sample.cc 46:22
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






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
- `-l` = **\<loc\>**: Core location in X-Y or R,C format


### Examples

Command:
```
cfg              Prints all configuration registers for current device and core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg -d 0         Prints all configuration reigsters for device with id 0 and current core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg -l 0,0       Pirnts all configuration registers for current device and core at location 0,0
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg all          Prints all configuration registers for current device and core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg alu          Prints alu configuration registers for current device and core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg pack         Prints packer's configuration registers for current device and core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
```
Command:
```
cfg unpack       Prints unpacker's configuration registers for current device and core
```
Output:
```
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]
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






## dbus

### Usage

```
debug-bus list-names [-v] [-d <device>] [-l <loc>]
debug-bus [<signals>] [-v] [-d <device>] [-l <loc>]
```


### Description

Commands for RISC-V debugging:
- list-names:    List all predefined debug bus signal names.
- [<signals>]:   List of signals described by signal name or signal description.
<signal-description>: DaisyId,RDSel,SigSel,Mask
-DaisyId - daisy chain identifier
-RDSel   - select 32bit data in 128bit register -> values [0-3]
-SigSel  - select 128bit register
-Mask    - 32bit number to show only significant bits (optional)
Examples:
debug-bus list-names                       # List predefined debug bus signals
debug-bus trisc0_pc,trisc1_pc              # Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
debug-bus [7,0,12,0x3ffffff],trisc2_pc     # Prints custom debug bus signal and trisc2_pc


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
Output:
```
RISC-V registers for location 0,0 on device 0
Register     BRISC       TRISC0    TRISC1    TRISC2
-----------  ----------  --------  --------  --------
0 - zero     0x00000000
1 - ra       0x00000b64
2 - sp       0xffb00fe0
3 - gp       0xffb00800
4 - tp       0x00000000
5 - t0       0x0000f640
6 - t1       0xffb00440
7 - t2       0xffb00440
8 - s0 / fp  0xffb00ff0
9 - s1       0x00000000
10 - a0      0x00000001
11 - a1      0xffb00ff0
12 - a2      0x00000000
13 - a3      0x00000000
14 - a4      0xffb1208c
15 - a5      0xffffedcc
16 - a6      0x00000000
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    BRISC       TRISC0    TRISC1    TRISC2
----------  ----------  --------  --------  --------
1 - ra      0x00000b64
2 - sp      0xffb00fe0
32 - pc     0x00000c40
Soft reset  0           1         1         1
Halted      False       -         -         -
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]
