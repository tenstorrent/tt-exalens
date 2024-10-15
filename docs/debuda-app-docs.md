## cdr

### Usage

```
cdr [ <core-loc> ]
```


### Description

Prints the state of the debug registers for core 'x-y'.
If coordinates are not supplied, it iterates through all cores.


### Arguments

- `core-loc`: Either X-Y or R,C location of the core


### Examples

Command:
```
cdr 18-18
```
Output:
```
=== Debug registers for core 18-18 ===
T0               T1               T2               FW
-------  ------  -------  ------  -------  ------  -------  ------
DBG[0]   0xbada  DBG[0]   0xbada  DBG[0]   0xbada  DBG[0]   0xbada
DBG[1]   0xda02  DBG[1]   0xda02  DBG[1]   0xda02  DBG[1]   0xda02
DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000
DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000
DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000
DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000
DBG[6]   0xbada  DBG[6]   0xbada  DBG[6]   0xbada  DBG[6]   0xbada
DBG[7]   0xbada  DBG[7]   0xbada  DBG[7]   0xbada  DBG[7]   0xbada
DBG[8]   0xbada  DBG[8]   0xbada  DBG[8]   0xbada  DBG[8]   0xbada
DBG[9]   0xbada  DBG[9]   0xbada  DBG[9]   0xbada  DBG[9]   0xbada
DBG[10]  0xbada  DBG[10]  0xbada  DBG[10]  0xbada  DBG[10]  0xbada
DBG[11]  0xbada  DBG[11]  0xbada  DBG[11]  0xbada  DBG[11]  0xbada
DBG[12]  0xbada  DBG[12]  0xbada  DBG[12]  0xbada  DBG[12]  0xbada
DBG[13]  0x0000  DBG[13]  0x0000  DBG[13]  0x0000  DBG[13]  0x0000
DBG[14]  0x0000  DBG[14]  0x0000  DBG[14]  0x0000  DBG[14]  0x0000
DBG[15]  0x0000  DBG[15]  0x0000  DBG[15]  0x0000  DBG[15]  0x0000
DBG[16]  0x0000  DBG[16]  0x0000  DBG[16]  0x0000  DBG[16]  0x0000
...
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
11  dram  harvested_workers  harvested_workers  harvested_workers  harvested_workers  dram  harvested_workers  harvested_workers  ...
10  arc   ----               ----               ----               ----               dram  ----               ----               ...
09        ----               ----               ----               ----               dram  ----               ----               ...
08        ----               ----               ----               ----               dram  ----               ----               ...
07  dram  ----               ----               ----               ----               dram  ----               ----               ...
06  dram  eth                eth                eth                eth                dram  eth                eth                ...
05  dram  harvested_workers  harvested_workers  harvested_workers  harvested_workers  dram  harvested_workers  harvested_workers  ...
04        ----               ----               ----               ----               dram  ----               ----               ...
03  pcie  ----               ----               ----               ----               dram  ----               ----               ...
02        ----               ----               ----               ----               dram  ----               ----               ...
01  dram  ----               ----               ----               ----               dram  ----               ----               ...
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
0x00000000:  00001234  827098af  cf8efc72  000000bb
0x00000010:  ffc00300  ffb00f9c  00000000  00000001
0x00000020:  00050004  004b0000  91800000  8e600001
0x00000030:  60000001  00000000  00000000  00000000
```
Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8             
```
Output:
```
18-18 (L1) : 0x00000000 (128 bytes)
0x00000000:  52  18  0    0    175  152  112  130  114  252  142  207  187  0  0   0
0x00000010:  0   3   192  255  156  15   176  255  0    0    0    0    1    0  0   0
0x00000020:  4   0   5    0    0    0    75   0    0    0    128  145  1    0  96  142
0x00000030:  1   0   0    96   0    0    0    0    0    0    0    0    0    0  0   0
0x00000040:  0   0   0    0    0    0    0    0    0    0    0    0    18   0  0   0
0x00000050:  0   0   0    0    0    0    54   0    0    0    0    0    0    0  0   0
0x00000060:  0   0   0    0    0    0    0    0    0    0    0    0    0    0  0   0
0x00000070:  0   0   0    0    0    0    0    0    0    0    0    0    0    0  0   0
```
Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5  
```
Output:
```
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 30087 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 30234 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 30210 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 30232 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 30175 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 30229 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 30247 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 30231 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 30209 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 30254 times
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
0x00000020:  c0193e34  be83bf68  3e70bdd6  3f883f8f
0x00000030:  3e04bebe  becbbfa7  3e2d3cb6  bebf3f72
```






