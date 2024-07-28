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

- **-pt \<point\>** : Index of the breakpoint or watchpoint register. 8 points are supported (0-7).


### Common options

- **--device, -d \<device-id\>** : Device ID. Defaults to the current device.
- **--loc, -l \<loc\>** : Grid location. Defaults to the current location.
- **--risc, -r \<risc-id\>** : RiscV ID (0: brisc, 1-3 triscs, all). [default: all]
- **--verbosity, -v \<verbosity\>** : Choose verbosity level. [default: 4]


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





## device / d


### Usage

```
device [<device-id> [<axis-coordinate> [<cell-contents>]]]
```


### Description

Shows a device summary. When no argument is supplied, it iterates through all devices used by the
currently loaded netlist.


### Arguments

- **device-id**:  ID of the device [default: 0]
- **axis-coordinate**:  Coordinate system for the axis [default: netlist] Supported: netlist, noc0, noc1, nocTr, nocVirt, die, tensix
- **cell-contents**:  A comma separated list of the cell contents [default: nocTr] Supported: op - show operation running on the core with epoch ID in parenthesis block - show the type of the block at that coordinate netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate


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


### Common options

- **--device, -d \<device-id\>** : Device ID. Defaults to the current device.
- **--loc, -l \<loc\>** : Grid location. Defaults to the current location.


### Examples

Command:
```
go -d 0 -l 0,0
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

- **reg-list** : List of registers to dump, comma-separated
- **elf-file** : Name of the elf file to use to resolve the source code location


### Common options

- **--device, -d \<device-id\>** : Device ID. Defaults to the current device.
- **--loc, -l \<loc\>** : Grid location. Defaults to the current location.
- **--verbosity, -v \<verbosity\>** : Choose verbosity level. [default: 4]
- **--risc, -r \<risc-id\>** : RiscV ID (0: brisc, 1-3 triscs, all). [default: all]


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





## re


### Usage

```
run-elf <elf-file> [ -v <verbosity> ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]
```


### Description

Loads an elf file into a brisc and runs it.


### Options

- **-r \<risc\>** : RiscV ID (0: brisc, 1-3 triscs). [default: 0]


### Common options

- **--device, -d \<device-id\>** : Device ID. Defaults to the current device.
- **--loc, -l \<loc\>** : Grid location. Defaults to the current location.
- **--verbosity, -v \<verbosity\>** : Choose verbosity level. [default: 4]
- **--risc, -r \<risc-id\>** : RiscV ID (0: brisc, 1-3 triscs, all). [default: all]


### Examples

Command:
```
run-elf build/risv-src/brisc-globals.elf
```





## cdr


### Usage

```
cdr [ <core-loc> ]
```


### Description

Prints the state of the debug registers for core 'x-y'.
If coordinates are not supplied, it iterates through all cores.


### Arguments

- **core-loc**:  Either X-Y or R,C location of the core


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
DBG[0]   0x004a  DBG[0]   0x004a  DBG[0]   0x004a  DBG[0]   0x004a
DBG[1]   0x3f99  DBG[1]   0x3f99  DBG[1]   0x3f99  DBG[1]   0x3f99
DBG[2]   0x5a31  DBG[2]   0x5a31  DBG[2]   0x5a31  DBG[2]   0x5a31
DBG[3]   0x5baa  DBG[3]   0x5baa  DBG[3]   0x5baa  DBG[3]   0x5baa
DBG[4]   0xe863  DBG[4]   0xe863  DBG[4]   0xe863  DBG[4]   0xe863
DBG[5]   0x627e  DBG[5]   0x627e  DBG[5]   0x627e  DBG[5]   0x627e
DBG[6]   0x1262  DBG[6]   0x1262  DBG[6]   0x1262  DBG[6]   0x1262
DBG[7]   0x8446  DBG[7]   0x8446  DBG[7]   0x8446  DBG[7]   0x8446
DBG[8]   0x80e0  DBG[8]   0x80e0  DBG[8]   0x80e0  DBG[8]   0x80e0
DBG[9]   0x9b05  DBG[9]   0x9b05  DBG[9]   0x9b05  DBG[9]   0x9b05
DBG[10]  0x641c  DBG[10]  0x641c  DBG[10]  0x641c  DBG[10]  0x641c
DBG[11]  0xcafb  DBG[11]  0xcafb  DBG[11]  0xcafb  DBG[11]  0xcafb
DBG[12]  0x0d12  DBG[12]  0x0d12  DBG[12]  0x0d12  DBG[12]  0x0d12
DBG[13]  0x0144  DBG[13]  0x0144  DBG[13]  0x0144  DBG[13]  0x0144
DBG[14]  0x6f64  DBG[14]  0x6f64  DBG[14]  0x6f64  DBG[14]  0x6f64
DBG[15]  0x551f  DBG[15]  0x551f  DBG[15]  0x551f  DBG[15]  0x551f
DBG[16]  0x7acb  DBG[16]  0x7acb  DBG[16]  0x7acb  DBG[16]  0x7acb
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

- **core-loc**:  Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- **addr**:  Address to read from
- **data**:  Data to write


### Examples

Command:
```
wxy 18-18 0x0 0x1234
```
Output:
```
18-18 0x00000000 (0) <= 0x00001234 (4660)
```





## brxy


### Usage

```
brxy <core-loc> <addr> [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <D>...]
```


### Description

Reads and prints a block of data from address 'addr' at core <core-loc>.


### Arguments

- **core-loc**:  Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
- **addr**:  Address to read from
- **word-count**:  Number of words to read. Default: 1


### Options

- **--sample \<N\>** : Number of seconds to sample for. [default: 0] (single read)
- **--format \<F\>** : Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
- **-o \<O\>** : Address offset. Optional and repeatable.
- **-d \<D\>** : Device ID. Optional and repeatable. Default: current device


### Examples

Read 1 word from address 0
```
brxy 18-18 0x0 1                          
```
Output:
```
L1-0x00000000-4
0x00000000:  00001234
```

Read 16 words from address 0
```
brxy 18-18 0x0 16                         
```
Output:
```
L1-0x00000000-64
0x00000000:  00001234  98c93f63  5eb28160  208bfc00
0x00000010:  f3524802  2e4142b1  a522a5cd  75be0646
0x00000020:  c054eb94  47bdf1fc  d009c606  12a65913
0x00000030:  6bc78a6e  5c14a753  a66b3432  16204562
```

Prints 32 bytes in i8 format
```
brxy 18-18 0x0 32 --format i8             
```
Output:
```
L1-0x00000000-128
0x00000000:  52   18   0    0    99   63   201  152  96   129  178  94   0    252  139  32
0x00000010:  2    72   82   243  177  66   65   46   205  165  34   165  70   6    190  117
0x00000020:  148  235  84   192  252  241  189  71   6    198  9    208  19   89   166  18
0x00000030:  110  138  199  107  83   167  20   92   50   52   107  166  98   69   32   22
0x00000040:  14   42   21   81   92   16   4    172  175  5    255  206  195  103  22   161
0x00000050:  24   188  252  139  6    104  107  89   162  10   64   199  15   46   100  243
0x00000060:  85   113  93   122  89   153  225  14   84   234  81   176  5    236  139  146
0x00000070:  112  125  125  32   90   223  169  47   147  196  46   40   104  193  171  1
```

Sample for 5 seconds
```
brxy 18-18 0x0 32 --format i8 --sample 5  
```
Output:
```
Sampling for 0.15625 seconds...
1-1 0x00000000 (0) => 0x00001234 (4660) - 31544 times
Sampling for 0.15625 seconds...
1-1 0x00000004 (4) => 0x00001234 (4660) - 31580 times
Sampling for 0.15625 seconds...
1-1 0x00000008 (8) => 0x00001234 (4660) - 31671 times
Sampling for 0.15625 seconds...
1-1 0x0000000c (12) => 0x00001234 (4660) - 31690 times
Sampling for 0.15625 seconds...
1-1 0x00000010 (16) => 0x00001234 (4660) - 31668 times
Sampling for 0.15625 seconds...
1-1 0x00000014 (20) => 0x00001234 (4660) - 31693 times
Sampling for 0.15625 seconds...
1-1 0x00000018 (24) => 0x00001234 (4660) - 31697 times
Sampling for 0.15625 seconds...
1-1 0x0000001c (28) => 0x00001234 (4660) - 31594 times
Sampling for 0.15625 seconds...
1-1 0x00000020 (32) => 0x00001234 (4660) - 31650 times
Sampling for 0.15625 seconds...
1-1 0x00000024 (36) => 0x00001234 (4660) - 31653 times
...
```

Read 16 words from dram channel 0
```
brxy ch0 0x0 16                           
```
Output:
```
L1-0x00000000-64
0x00000000:  000000fb  55555555  55555555  55555555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  7d510050  50455050  45215580  40f04045
0x00000030:  55105554  51755554  55545554  51755175
```





