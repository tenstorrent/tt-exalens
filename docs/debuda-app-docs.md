## rv

### Usage

```
riscv (halt | step | cont | status) [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
riscv rd [<address>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
riscv rreg [<index>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
riscv wr [<address>] [<data>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
riscv wreg [<index>] [<data>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
riscv bkpt (set | del) [<address>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv wchpt (setr | setw | setrw | del) [<address>] [<data>] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>] [-pt <point>]
riscv reset [1 | 0] [-v <verbosity>] [-d <device>] [-r <risc>] [-l <loc>]
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
- `--verbosity, -v` = **\<verbosity\>**: Choose verbosity level. [default: 4]






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
- `cell-contents`: A comma separated list of the cell contents [default: nocTr] Supported: op - show operation running on the core with epoch ID in parenthesis block - show the type of the block at that coordinate netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate


### Examples

Shows op mapping for all devices
```
device             
```
Output:
```
==== Device 0
    00     01     02     03     04     05     06     07
00  18-18  19-18  20-18  21-18  22-18  23-18  24-18  25-18
01  18-19  19-19  20-19  21-19  22-19  23-19  24-19  25-19
02  18-20  19-20  20-20  21-20  22-20  23-20  24-20  25-20
03  18-21  19-21  20-21  21-21  22-21  23-21  24-21  25-21
04  18-22  19-22  20-22  21-22  22-22  23-22  24-22  25-22
05  18-23  19-23  20-23  21-23  22-23  23-23  24-23  25-23
06  18-24  19-24  20-24  21-24  22-24  23-24  24-24  25-24
07  18-25  19-25  20-25  21-25  22-25  23-25  24-25  25-25
08  18-26  19-26  20-26  21-26  22-26  23-26  24-26  25-26
```
Shows noc0 to nocTr mapping for device 0
```
device 0 noc0      
```
Output:
```
==== Device 0
11  16-27  18-27  19-27  20-27  21-27  17-27  22-27  23-27  24-27  25-27
10  16-26  18-26  19-26  20-26  21-26  17-26  22-26  23-26  24-26  25-26
09         18-25  19-25  20-25  21-25  17-25  22-25  23-25  24-25  25-25
08         18-24  19-24  20-24  21-24  17-24  22-24  23-24  24-24  25-24
07  16-23  18-23  19-23  20-23  21-23  17-23  22-23  23-23  24-23  25-23
06  16-17  18-17  19-17  20-17  21-17  17-17  22-17  23-17  24-17  25-17
05  16-22  18-22  19-22  20-22  21-22  17-22  22-22  23-22  24-22  25-22
04         18-21  19-21  20-21  21-21  17-21  22-21  23-21  24-21  25-21
03  16-20  18-20  19-20  20-20  21-20  17-20  22-20  23-20  24-20  25-20
02         18-19  19-19  20-19  21-19  17-19  22-19  23-19  24-19  25-19
01  16-18  18-18  19-18  20-18  21-18  17-18  22-18  23-18  24-18  25-18
00  16-16  18-16  19-16  20-16  21-16  17-16  22-16  23-16  24-16  25-16
    00     01     02     03     04     05     06     07     08     09
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






## gpr

### Usage

```
gpr [ <reg-list> ] [ <elf-file> ] [ -v <verbosity> ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]
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
  enable_debug()
    __riscv_write(1, 0x80000000)
CNTL1 <- WR   0x80000000
      __trigger_write(1)
CNTL0 <- WR   0x80010001
CNTL0 <- WR   0x00000000
  is_halted()
  read_status()
  __riscv_read(0)
      __trigger_read(0)
CNTL0 <- WR   0x80000000
CNTL0 <- WR   0x00000000
  __is_read_valid()
STATUS0 -> RD == 0x40000000
STATUS1 -> RD == 0x00000000
  is_halted()
  read_status()
  __riscv_read(0)
      __trigger_read(0)
CNTL0 <- WR   0x80000000
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
  enable_debug()
    __riscv_write(1, 0x80000000)
CNTL1 <- WR   0x80000000
      __trigger_write(1)
CNTL0 <- WR   0x80010001
CNTL0 <- WR   0x00000000
  is_halted()
  read_status()
  __riscv_read(0)
      __trigger_read(0)
CNTL0 <- WR   0x80000000
CNTL0 <- WR   0x00000000
  __is_read_valid()
STATUS0 -> RD == 0x40000000
STATUS1 -> RD == 0x00000000
  is_halted()
  read_status()
  __riscv_read(0)
      __trigger_read(0)
CNTL0 <- WR   0x80000000
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbosity, -v` = **\<verbosity\>**: Choose verbosity level. [default: 4]
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]






## re

### Usage

```
run-elf <elf-file> [ -v <verbosity> ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]
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
- `--verbosity, -v` = **\<verbosity\>**: Choose verbosity level. [default: 4]






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
DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000
DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000
DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000
DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000
DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000  DBG[4]   0x0000
DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000  DBG[5]   0x0000
DBG[6]   0x0000  DBG[6]   0x0000  DBG[6]   0x0000  DBG[6]   0x0000
DBG[7]   0x0000  DBG[7]   0x0000  DBG[7]   0x0000  DBG[7]   0x0000
DBG[8]   0x0000  DBG[8]   0x0000  DBG[8]   0x0000  DBG[8]   0x0000
DBG[9]   0x0000  DBG[9]   0x0000  DBG[9]   0x0000  DBG[9]   0x0000
DBG[10]  0x0000  DBG[10]  0x0000  DBG[10]  0x0000  DBG[10]  0x0000
DBG[11]  0x0000  DBG[11]  0x0000  DBG[11]  0x0000  DBG[11]  0x0000
DBG[12]  0xfe54  DBG[12]  0xfe54  DBG[12]  0xfe54  DBG[12]  0xfe54
DBG[13]  0xee87  DBG[13]  0xee87  DBG[13]  0xee87  DBG[13]  0xee87
DBG[14]  0xd7ed  DBG[14]  0xd7ed  DBG[14]  0xd7ed  DBG[14]  0xd7ed
DBG[15]  0x6283  DBG[15]  0x6283  DBG[15]  0x6283  DBG[15]  0x6283
DBG[16]  0xe8b4  DBG[16]  0xe8b4  DBG[16]  0xe8b4  DBG[16]  0xe8b4
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
0x00000000:  00001234  876545b7  00b52023  0000006f
0x00000010:  0000006f  00b52023  ff9ff06f  000000bb
0x00000020:  00080009  002c000a  00018f80  00300000
0x00000030:  0030000c  0030002c  11070100  00000a02
```
Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8             
```
Output:
```
18-18 (L1) : 0x00000000 (128 bytes)
0x00000000:  52   18   0    0    183  69   101  135  35   32   181  0    111  0    0    0
0x00000010:  111  0    0    0    35   32   181  0    111  240  159  255  187  0    0    0
0x00000020:  9    0    8    0    10   0    44   0    128  143  1    0    0    0    48   0
0x00000030:  12   0    48   0    44   0    48   0    0    1    7    17   2    10   0    0
0x00000040:  0    0    0    0    2    0    0    0    88   0    0    0    88   0    0    0
0x00000050:  88   0    0    0    88   0    0    0    88   0    0    0    88   0    0    0
0x00000060:  218  186  218  186  218  186  218  186  218  186  218  186  218  186  218  186
0x00000070:  218  186  2    0    218  186  0    0    218  186  218  186  218  186  218  186
```
Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5  
```
Output:
```
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 28789 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 28892 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 28716 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 28849 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 28878 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 28735 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 28832 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 28850 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 28703 times
Sampling for 0.15625 seconds...
18-18 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 28840 times
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
0x00000020:  55555555  55555555  55555555  55555555
0x00000030:  55555555  55555555  55555555  55555555
```






