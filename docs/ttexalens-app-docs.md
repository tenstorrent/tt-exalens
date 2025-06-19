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
0x00000000:  2010006f  56d34d03  0226161b  000000bb
0x00000010:  ffc00000  ffb00f70  80808000  00000000
0x00000020:  00040005  002f0006  000067d0  0003f520
0x00000030:  000073d0  00000020  00200000  00000130
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
0,0 (L1) : 0x00000000 (128 bytes)
0x00000000:  111  0    16   32   3    77  211  86   27   22   38   2    187  0    0  0
0x00000010:  0    0    192  255  112  15  176  255  0    128  128  128  0    0    0  0
0x00000020:  5    0    4    0    6    0   47   0    208  103  0    0    32   245  3  0
0x00000030:  208  115  0    0    32   0   0    0    0    0    32   0    48   1    0  0
0x00000040:  32   0    8    0    32   0   24   0    32   0    0    0    48   1    0  0
0x00000050:  48   3    0    0    32   6   0    0    144  10   0    0    192  12   0  0
0x00000060:  0    0    0    17   32   0   0    0    0    0    0    0    7    0    0  128
0x00000070:  0    0    0    0    0    0   72   0    0    0    0    0    0    0    0  0
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000000 (0) => 0x2010006f (537919599) - 13420 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x2010006f (537919599) - 13635 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x2010006f (537919599) - 13653 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x2010006f (537919599) - 13499 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x2010006f (537919599) - 13668 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x2010006f (537919599) - 13399 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x2010006f (537919599) - 13354 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x2010006f (537919599) - 13568 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x2010006f (537919599) - 13520 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x2010006f (537919599) - 13612 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  000000bb  55555555  55555551  55555555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  41604160  41604160  41604160  41604160
0x00000030:  41604160  41604160  41604160  41604160
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## bt

### Usage

```
callstack <elf-files> [-o <offsets>] [-r <risc>] [-m <max-depth>] [-v] [-d <device>] [-l <loc>]
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
Location: 1-1 (0,0), core: brisc
  #0  0x00000BC8 in halt () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 33:1
  #1  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #2  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #3  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #4  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #5  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #6  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #7  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #8  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #9  0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #10 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #11 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #12 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #13 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #14 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #15 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #16 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #17 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
  #18 0x00000C00 in infloop () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 37:27
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## dbus

### Usage

```
debug-bus list-names [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
debug-bus [<signals>] [-v] [-d <device>] [-l <loc>]
```


### Description

Commands for RISC-V debugging:
- list-names:    List all predefined debug bus signal names.
--search:
- [<signals>]:   List of signals described by signal name or signal description.
<signal-description>: {DaisyId,RDSel,SigSel,Mask}
-DaisyId - daisy chain identifier
-RDSel   - select 32bit data in 128bit register -> values [0-3]
-SigSel  - select 128bit register
-Mask    - 32bit number to show only significant bits (optional)


### Options

- `-s,` = **--simple**: Print simple output
- `--search` = **\<pattern\>**: Search for signals by pattern (in wildcard format)
- `--max` = **\<max-sigs\>**: Limit --search output (default: 10, use --max "all" to print all matches)


### Examples

List predefined debug bus signals
```
debug-bus list-names
```
Output:
```
=== Device 0 - location 0,0)
        Signals
╭─────────────┬────────╮
│ Description │ Value  │
├─────────────┼────────┤
│ brisc_pc    │ 0xbc8  │
│ trisc0_pc   │ 0x7148 │
│ trisc1_pc   │ 0x7468 │
│ trisc2_pc   │ 0x781c │
│ ncrisc_pc   │ 0x4f20 │
╰─────────────┴────────╯

```
List up to 5 signals whose names contain pc
```
debug-bus list-names --search *pc* --max 5
```
Output:
```
=== Device 0 - location 0,0)
        Signals
╭─────────────┬────────╮
│ Description │ Value  │
├─────────────┼────────┤
│ brisc_pc    │ 0xbc8  │
│ trisc0_pc   │ 0x7148 │
│ trisc1_pc   │ 0x7468 │
│ trisc2_pc   │ 0x781c │
│ ncrisc_pc   │ 0x4efc │
╰─────────────┴────────╯

```
Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
```
debug-bus trisc0_pc,trisc1_pc
```
Output:
```
device:0 loc:1-1 (0,0)  trisc0_pc: 0x7148
device:0 loc:1-1 (0,0)  trisc1_pc: 0x7468
```
Prints custom debug bus signal and trisc2_pc
```
debug-bus {7,0,12,0x3ffffff},trisc2_pc
```
Output:
```
device:0 loc:1-1 (0,0)  Debug Bus Config(Daisy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff) = 0x7148
device:0 loc:1-1 (0,0)  trisc2_pc: 0x781c
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
00  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
01  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
02  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
03  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
04  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
05  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
06  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
07  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR  RRRRR
==== Device 1
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
01  dram         RRRRR  RRRRR  RRRRR  RRRRR  dram  RRRRR  RRRRR  RRRRR  RRRRR
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
04  1-7   2-7   3-7   4-7   6-7   7-7   8-7   9-7
05  1-8   2-8   3-8   4-8   6-8   7-8   8-8   9-8
06  1-9   2-9   3-9   4-9   6-9   7-9   8-9   9-9
07  1-10  2-10  3-10  4-10  6-10  7-10  8-10  9-10
==== Device 1
    00    01    02    03    04    05    06    07
00  1-2   2-2   3-2   4-2   6-2   7-2   8-2   9-2
...
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
05  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
11  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
==== Device 1
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
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
05  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
11  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
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
┌───────────────────┬────────────────────┐
│ ALU CONFIG        │ VALUES             │
├───────────────────┼────────────────────┤
│ Fpu_srnd_en       │ False              │
│ Gasket_srnd_en    │ False              │
│ Packer_srnd_en    │ False              │
│ Padding           │ 0                  │
│ GS_LF             │ False              │
│ Bfp8_HF           │ False              │
│ SrcAUnsigned      │ False              │
│ SrcBUnsigned      │ False              │
│ Format_SrcA       │ 5 -> INVALID VALUE │
│ Format_SrcB       │ 5 -> INVALID VALUE │
│ Format_Dstacc     │ 5 -> INVALID VALUE │
│ Fp32_enabled      │ False              │
│ SFPU_Fp32_enabled │ False              │
│ INT8_math_enabled │ False              │
└───────────────────┴────────────────────┘
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
┌───────────────────┬────────────────────┐
│ ALU CONFIG        │ VALUES             │
├───────────────────┼────────────────────┤
│ Fpu_srnd_en       │ False              │
│ Gasket_srnd_en    │ False              │
│ Packer_srnd_en    │ False              │
│ Padding           │ 0                  │
│ GS_LF             │ False              │
│ Bfp8_HF           │ False              │
│ SrcAUnsigned      │ False              │
│ SrcBUnsigned      │ False              │
│ Format_SrcA       │ 5 -> INVALID VALUE │
│ Format_SrcB       │ 5 -> INVALID VALUE │
│ Format_Dstacc     │ 5 -> INVALID VALUE │
│ Fp32_enabled      │ False              │
│ SFPU_Fp32_enabled │ False              │
│ INT8_math_enabled │ False              │
└───────────────────┴────────────────────┘
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
┌───────────────────┬────────────────────┐
│ ALU CONFIG        │ VALUES             │
├───────────────────┼────────────────────┤
│ Fpu_srnd_en       │ False              │
│ Gasket_srnd_en    │ False              │
│ Packer_srnd_en    │ False              │
│ Padding           │ 0                  │
│ GS_LF             │ False              │
│ Bfp8_HF           │ False              │
│ SrcAUnsigned      │ False              │
│ SrcBUnsigned      │ False              │
│ Format_SrcA       │ 5 -> INVALID VALUE │
│ Format_SrcB       │ 5 -> INVALID VALUE │
│ Format_Dstacc     │ 5 -> INVALID VALUE │
│ Fp32_enabled      │ False              │
│ SFPU_Fp32_enabled │ False              │
│ INT8_math_enabled │ False              │
└───────────────────┴────────────────────┘
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
┌───────────────────┬────────────────────┐
│ ALU CONFIG        │ VALUES             │
├───────────────────┼────────────────────┤
│ Fpu_srnd_en       │ False              │
│ Gasket_srnd_en    │ False              │
│ Packer_srnd_en    │ False              │
│ Padding           │ 0                  │
│ GS_LF             │ False              │
│ Bfp8_HF           │ False              │
│ SrcAUnsigned      │ False              │
│ SrcBUnsigned      │ False              │
│ Format_SrcA       │ 5 -> INVALID VALUE │
│ Format_SrcB       │ 5 -> INVALID VALUE │
│ Format_Dstacc     │ 5 -> INVALID VALUE │
│ Fp32_enabled      │ False              │
│ SFPU_Fp32_enabled │ False              │
│ INT8_math_enabled │ False              │
└───────────────────┴────────────────────┘
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
┌───────────────────┬────────────────────┐
│ ALU CONFIG        │ VALUES             │
├───────────────────┼────────────────────┤
│ Fpu_srnd_en       │ False              │
│ Gasket_srnd_en    │ False              │
│ Packer_srnd_en    │ False              │
│ Padding           │ 0                  │
│ GS_LF             │ False              │
│ Bfp8_HF           │ False              │
│ SrcAUnsigned      │ False              │
│ SrcBUnsigned      │ False              │
│ Format_SrcA       │ 5 -> INVALID VALUE │
│ Format_SrcB       │ 5 -> INVALID VALUE │
│ Format_Dstacc     │ 5 -> INVALID VALUE │
│ Fp32_enabled      │ False              │
│ SFPU_Fp32_enabled │ False              │
│ INT8_math_enabled │ False              │
└───────────────────┴────────────────────┘
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
┌────────────────────────────────────┬────────────────────┬────────────────────┬────────────────────┬────────────────────┐
│ PACK CONFIG                        │ REG_ID = 1         │ REG_ID = 2         │ REG_ID = 3         │ REG_ID = 4         │
├────────────────────────────────────┼────────────────────┼────────────────────┼────────────────────┼────────────────────┤
│ row_ptr_section_size               │ 0                  │ 0                  │ 0                  │ 0                  │
│ exp_section_size                   │ 4                  │ 4                  │ 4                  │ 4                  │
│ l1_dest_addr                       │ 0x0                │ 0x1f               │ 0x3f               │ 0x5f               │
│ uncompress                         │ True               │ True               │ True               │ True               │
│ add_l1_dest_addr_offset            │ False              │ False              │ False              │ False              │
│ reserved_0                         │ 0                  │ 0                  │ 0                  │ 0                  │
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
┌─────────────────────────┬────────────────────┬────────────────────┐   ┌────────────────────┬────────────────────┬───────────────...
│ UNPACK CONFIG           │ REG_ID = 1         │ REG_ID = 2         │   │ TILE DESCRIPTOR    │ REG_ID = 1         │ REG_ID = 2    ...
├─────────────────────────┼────────────────────┼────────────────────┤   ├────────────────────┼────────────────────┼───────────────...
│ out_data_format         │ 5 -> INVALID VALUE │ 5 -> INVALID VALUE │   │ in_data_format     │ 5 -> INVALID VALUE │ 5 -> INVALID V...
│ throttle_mode           │ 2                  │ 2                  │   │ uncompressed       │ True               │ True          ...
│ context_count           │ 0                  │ 0                  │   │ reserved_0         │ 0                  │ 0             ...
│ haloize_mode            │ 0                  │ 0                  │   │ blobs_per_xy_plane │ 0                  │ 0             ...
│ tileize_mode            │ 0                  │ 0                  │   │ reserved_1         │ 0                  │ 0             ...
│ unpack_src_reg_set_upd  │ False              │ False              │   │ x_dim              │ 0                  │ 256           ...
│ unpack_if_sel           │ False              │ False              │   │ y_dim              │ 1                  │ 1             ...
│ upsample_rate           │ 0                  │ 0                  │   │ z_dim              │ 4                  │ 4             ...
│ reserved_1              │ 0                  │ 0                  │   │ w_dim              │ 0                  │ 0             ...
│ upsample_and_interleave │ False              │ False              │   │ digest_type        │ 0                  │ 0             ...
│ shift_amount            │ 0                  │ 0                  │   │ digest_size        │ 0                  │ 0             ...
│ uncompress_cntx0_3      │ 15                 │ 15                 │   │ blobs_y_start      │ 0                  │ 0             ...
│ unpack_if_sel_cntx0_3   │ 0                  │ 0                  │   └────────────────────┴────────────────────┴───────────────...
│ force_shared_exp        │ False              │ False              │                                                             ...
│ reserved_2              │ 0                  │ 0                  │                                                             ...
...
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
Register     brisc       trisc0      trisc1      trisc2      ncrisc
-----------  ----------  ----------  ----------  ----------  --------
0 - zero     0x00000000  0x00000000  0x00000000  0x00000000
1 - ra       0x00000c00  0x000058fc  0x00005d4c  0x000064e8
2 - sp       0xffb00e60  0xffb00780  0xffb007a0  0xffb00790
3 - gp       0xffb00800  0xffb007f0  0xffb007f0  0xffb007f0
4 - tp       0x00000000  0x00000000  0x00000000  0x00000000
5 - t0       0x0000f638  0x00000000  0x00000000  0x00000000
6 - t1       0xffb00438  0x00000000  0x00000000  0x45003f3c
7 - t2       0xffb00438  0x00000000  0x00000000  0x00000000
8 - s0 / fp  0xffb00e70  0x00000000  0x00000000  0x00000000
9 - s1       0x00000000  0x00000000  0x00000000  0x00000000
10 - a0      0x00000001  0x000017bd  0x02000000  0xffe80000
11 - a1      0xffb00ff0  0x0000183d  0xb2010000  0x4500200c
12 - a2      0x00000000  0xffef0000  0x00000008  0x41008f11
13 - a3      0x00000000  0xffe80000  0xffe40000  0xffb00020
14 - a4      0x00000001  0xffb00020  0x00000000  0xffe40000
15 - a5      0x00000001  0x00000001  0xb2010200  0xb0048098
16 - a6      0x00000000  0x00000000  0x00000000  0x5e83fc00
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    brisc       trisc0      trisc1      trisc2      ncrisc
----------  ----------  ----------  ----------  ----------  --------
1 - ra      0x00000c00  0x000058fc  0x00005d4c  0x000064e8
2 - sp      0xffb00e60  0xffb00780  0xffb007a0  0xffb00790
32 - pc     0x00000bc8  0x00007148  0x00007468  0x0000781c
Soft reset  False       False       False       False       False
Halted      True        True        True        True        ?
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
          Transaction Counters (Sent)                       Transaction Counters (Received)
╭────────────────────────────┬────────────────╮ ╭────────────────────────────────┬─────────────────────╮
│ Description                │ Value          │ │ Description                    │ Value               │
├────────────────────────────┼────────────────┤ ├────────────────────────────────┼─────────────────────┤
│ nonposted write reqs sent  │ 0x00000000 (0) │ │ nonposted write reqs received  │ 0x00003971 (14705)  │
│ posted write reqs sent     │ 0x00000000 (0) │ │ posted write reqs received     │ 0x00000000 (0)      │
│ nonposted write words sent │ 0x00000000 (0) │ │ nonposted write words received │ 0x00003afd (15101)  │
│ posted write words sent    │ 0x00000000 (0) │ │ posted write words received    │ 0x00000000 (0)      │
│ write acks received        │ 0x00000000 (0) │ │ write acks sent                │ 0x00003971 (14705)  │
│ read reqs sent             │ 0x00000000 (0) │ │ read reqs received             │ 0x0006bb26 (441126) │
│ read words received        │ 0x00000000 (0) │ │ read words sent                │ 0x0006bb26 (441126) │
│ read resps received        │ 0x00000000 (0) │ │ read resps sent                │ 0x0006bb27 (441127) │
╰────────────────────────────┴────────────────╯ ╰────────────────────────────────┴─────────────────────╯

NOC1 Status Registers
           Transaction Counters (Sent)                      Transaction Counters (Received)
╭────────────────────────────┬──────────────────╮ ╭────────────────────────────────┬─────────────────╮
│ Description                │ Value            │ │ Description                    │ Value           │
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

  nonposted write reqs sent    0x00000000 (0)
  posted write reqs sent       0x00000000 (0)
  nonposted write words sent   0x00000000 (0)
  posted write words sent      0x00000000 (0)
  write acks received          0x00000000 (0)
  read reqs sent               0x00000000 (0)
  read words received          0x00000000 (0)
  read resps received          0x00000000 (0)


            Transaction Counters (Received)

  nonposted write reqs received    0x00003971 (14705)
  posted write reqs received       0x00000000 (0)
  nonposted write words received   0x00003afd (15101)
  posted write words received      0x00000000 (0)
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
╭─────────────────────┬────────────────╮
│ Description         │ Value          │
├─────────────────────┼────────────────┤
│ NIU_MST_RD_REQ_SENT │ 0x00000000 (0) │
╰─────────────────────┴────────────────╯

             NOC1 Registers
╭─────────────────────┬────────────────╮
│ Description         │ Value          │
├─────────────────────┼────────────────┤
│ NIU_MST_RD_REQ_SENT │ 0x00000002 (2) │
╰─────────────────────┴────────────────╯

```
Prints multiple registers
```
noc register NIU_MST_RD_REQ_SENT,NIU_MST_RD_DATA_WORD_RECEIVED
```
Output:
```
==== Device 0 - Location: 1-1
                  NOC0 Registers
╭───────────────────────────────┬────────────────╮
│ Description                   │ Value          │
├───────────────────────────────┼────────────────┤
│ NIU_MST_RD_REQ_SENT           │ 0x00000000 (0) │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0x00000000 (0) │
╰───────────────────────────────┴────────────────╯

                   NOC1 Registers
╭───────────────────────────────┬──────────────────╮
│ Description                   │ Value            │
├───────────────────────────────┼──────────────────┤
│ NIU_MST_RD_REQ_SENT           │ 0x00000002 (2)   │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0x00000080 (128) │
╰───────────────────────────────┴──────────────────╯

```
Show all registers that have "_RD" in their name
```
noc register --search *_RD* --max all
```
Output:
```
==== Device 0 - Location: 1-1
                    NOC0 Registers
╭───────────────────────────────┬─────────────────────╮
│ Description                   │ Value               │
├───────────────────────────────┼─────────────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0x00000000 (0)      │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0x00000000 (0)      │
│ NIU_MST_RD_REQ_SENT           │ 0x00000000 (0)      │
│ NIU_MST_RD_REQ_STARTED        │ 0x00000000 (0)      │
│ NIU_SLV_RD_RESP_SENT          │ 0x0006bb62 (441186) │
│ NIU_SLV_RD_DATA_WORD_SENT     │ 0x0006bb63 (441187) │
│ NIU_SLV_RD_REQ_RECEIVED       │ 0x0006bb65 (441189) │
╰───────────────────────────────┴─────────────────────╯

                   NOC1 Registers
╭───────────────────────────────┬──────────────────╮
│ Description                   │ Value            │
├───────────────────────────────┼──────────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0x00000002 (2)   │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0x00000080 (128) │
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
Output:
```
Halting brisc 0,0 [0]
Halt: brisc core at 0,0 is already halted
Halting trisc0 0,0 [0]
Halt: trisc0 core at 0,0 is already halted
Halting trisc1 0,0 [0]
Halt: trisc1 core at 0,0 is already halted
Halting trisc2 0,0 [0]
Halt: trisc2 core at 0,0 is already halted
```
Print status
```
riscv status
```
Output:
```
  HALTED PC=0x00000bc8 - brisc 0,0 [0]
  HALTED PC=0x00007148 - trisc0 0,0 [0]
  HALTED PC=0x00007468 - trisc1 0,0 [0]
  HALTED PC=0x0000781c - trisc2 0,0 [0]
```
Step
```
riscv step
```
Output:
```
Stepping brisc 0,0 [0]
Stepping trisc0 0,0 [0]
Stepping trisc1 0,0 [0]
Stepping trisc2 0,0 [0]
```
Continue
```
riscv cont
```
Output:
```
Continuing brisc 0,0 [0]
Continue: brisc core at 0,0 is already running
Continuing trisc0 0,0 [0]
Continue: trisc0 core at 0,0 is already running
Continuing trisc1 0,0 [0]
Continuing trisc2 0,0 [0]
Continue: trisc2 core at 0,0 is already running
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
Output:
```
Writing to register 1 on brisc 0,0 [0]
Writing to register 1 on trisc0 0,0 [0]
Writing to register 1 on trisc1 0,0 [0]
Writing to register 1 on trisc2 0,0 [0]
```
Read a word from register 1
```
riscv rreg 1
```
Output:
```
Reading from register 1 on brisc 0,0 [0]
  0x00000bc8
Reading from register 1 on trisc0 0,0 [0]
  0x00007148
Reading from register 1 on trisc1 0,0 [0]
  0x80008000
Reading from register 1 on trisc2 0,0 [0]
  0x0000781c
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
5
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
5 -> INVALID VALUE
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, raw_ad...
5 -> INVALID VALUE
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
Output:
```
Register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, raw_address=Non...
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
