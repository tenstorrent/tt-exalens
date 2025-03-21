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
Output:
```
Halting BRISC 0,0 [0]
Halting TRISC0 0,0 [0]
Halting TRISC1 0,0 [0]
Halting TRISC2 0,0 [0]
```
Print status
```
riscv status
```
Output:
```
  HALTED PC=0x00000c58 - BRISC 0,0 [0]
  HALTED PC=0x00006000 - TRISC0 0,0 [0]
  HALTED PC=0x0000a000 - TRISC1 0,0 [0]
  HALTED PC=0x0000e000 - TRISC2 0,0 [0]
```
Step
```
riscv step
```
Output:
```
Stepping BRISC 0,0 [0]
Stepping TRISC0 0,0 [0]
Stepping TRISC1 0,0 [0]
Stepping TRISC2 0,0 [0]
```
Continue
```
riscv cont
```
Output:
```
Continuing BRISC 0,0 [0]
Continuing TRISC0 0,0 [0]
Continuing TRISC1 0,0 [0]
Continuing TRISC2 0,0 [0]
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
Writing to register 1 on BRISC 0,0 [0]
Writing to register 1 on TRISC0 0,0 [0]
Writing to register 1 on TRISC1 0,0 [0]
Writing to register 1 on TRISC2 0,0 [0]
```
Read a word from register 1
```
riscv rreg 1
```
Output:
```
Reading from register 1 on BRISC 0,0 [0]
  0xffb1208c
Reading from register 1 on TRISC0 0,0 [0]
  0x00006000
Reading from register 1 on TRISC1 0,0 [0]
  0x0000a000
Reading from register 1 on TRISC2 0,0 [0]
  0x0000e000
```
Set breakpoint
```
riscv bkpt set 0 0x1244
```
Output:
```
Setting breakpoint at address 0 for BRISC 0,0 [0]
Setting breakpoint at address 0 for TRISC0 0,0 [0]
Setting breakpoint at address 0 for TRISC1 0,0 [0]
Setting breakpoint at address 0 for TRISC2 0,0 [0]
```
Delete breakpoint
```
riscv bkpt del 0
```
Output:
```
Deleting breakpoint 0 for BRISC 0,0 [0]
Deleting breakpoint 0 for TRISC0 0,0 [0]
Deleting breakpoint 0 for TRISC1 0,0 [0]
Deleting breakpoint 0 for TRISC2 0,0 [0]
```
Set a read watchpoint
```
riscv wchpt setr 0 0xc
```
Output:
```
Setting read watchpoint at address 0 for BRISC 0,0 [0]
Setting read watchpoint at address 0 for TRISC0 0,0 [0]
Setting read watchpoint at address 0 for TRISC1 0,0 [0]
Setting read watchpoint at address 0 for TRISC2 0,0 [0]
```
Set a write watchpoint
```
riscv wchpt setw 0 0xc
```
Output:
```
Setting write watchpoint at address 0 for BRISC 0,0 [0]
Setting write watchpoint at address 0 for TRISC0 0,0 [0]
Setting write watchpoint at address 0 for TRISC1 0,0 [0]
Setting write watchpoint at address 0 for TRISC2 0,0 [0]
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]
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

Prints all configuration registers for current device and core
```
cfg
```
Output:
```
all
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
...
```
Prints all configuration reigsters for device with id 0 and current core
```
cfg -d 0
```
Output:
```
all
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
...
```
Pirnts all configuration registers for current device and core at location 0,0
```
cfg -l 0,0
```
Output:
```
all
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
...
```
Prints all configuration registers for current device and core
```
cfg all
```
Output:
```
all
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
...
```
Prints alu configuration registers for current device and core
```
cfg alu
```
Output:
```
alu
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
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
...
```
Prints packer's configuration registers for current device and core
```
cfg pack
```
Output:
```
pack
Configuration registers for location 0,0 on device 0
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
...
```
Prints unpacker's configuration registers for current device and core
```
cfg unpack
```
Output:
```
unpack
Configuration registers for location 0,0 on device 0
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
│ upsample_and_interleave │ False                    │ False                    │   │ digest_type        │ 0                      ...
│ shift_amount            │ 0                        │ 0                        │   │ digest_size        │ 0                      ...
│ uncompress_cntx0_3      │ 0                        │ 0                        │   │ blobs_y_start      │ 0                      ...
│ unpack_if_sel_cntx0_3   │ 0                        │ 0                        │   └────────────────────┴────────────────────────...
│ force_shared_exp        │ False                    │ False                    │                                                 ...
...
```






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
00  RRRR  ----  ----  ----  ----  ----  ----  ----
01  ----  RRRR  ----  ----  ----  ----  ----  ----
02  ----  ----  RRRR  ----  ----  ----  ----  ----
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
01  dram  RRRR  ----  ----  ----  dram  ----  ----  ----  ----
02        ----  RRRR  ----  ----  dram  ----  ----  ----  ----
03  pcie  ----  ----  RRRR  ----  dram  ----  ----  ----  ----
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
02  dram  ----  RRRR  ----  ----  ----  ----  ----  ----  dram
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
Register     BRISC       TRISC0      TRISC1      TRISC2
-----------  ----------  ----------  ----------  ----------
0 - zero     0x00000000  0x00000000  0x00000000  0x00000000
1 - ra       0x00000b64  0x00000000  0x00000000  0x00000000
2 - sp       0xffb00fe0  0x00000000  0x00000000  0x00000000
3 - gp       0xffb00800  0x00000000  0x00000000  0x00000000
4 - tp       0x00000000  0x00000000  0x00000000  0x00000000
5 - t0       0x0000f640  0x00000000  0x00000000  0x00000000
6 - t1       0xffb00440  0x00000000  0x00000000  0x00000000
7 - t2       0xffb00440  0x00000000  0x00000000  0x00000000
8 - s0 / fp  0xffb00ff0  0x00000000  0x00000000  0x00000000
9 - s1       0x00000000  0x00000000  0x00000000  0x00000000
10 - a0      0x00000001  0x00000000  0x00000000  0x00000000
11 - a1      0xffb00ff0  0x00000000  0x00000000  0x00000000
12 - a2      0x00000000  0x00000000  0x00000000  0x00000000
13 - a3      0x00000000  0x00000000  0x00000000  0x00000000
14 - a4      0xffb1208c  0x00000000  0x00000000  0x00000000
15 - a5      0xffb10e58  0x00000000  0x00000000  0x00000000
16 - a6      0x00000000  0x00000000  0x00000000  0x00000000
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    BRISC       TRISC0      TRISC1      TRISC2
----------  ----------  ----------  ----------  ----------
1 - ra      0x00000b64  0x00000000  0x00000000  0x00000000
2 - sp      0xffb00fe0  0x00000000  0x00000000  0x00000000
32 - pc     0x00000c40  0x00006000  0x0000a000  0x0000e000
Soft reset  0           0           0           0
Halted      False       False       False       False
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
0x00000000:  2010006f  deadbeef  deadbeef  deadbeef
0x00000010:  deadbeef  deadbeef  deadbeef  deadbeef
0x00000020:  deadbeef  deadbeef  deadbeef  deadbeef
0x00000030:  deadbeef  deadbeef  deadbeef  deadbeef
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
0,0 (L1) : 0x00000000 (128 bytes)
0x00000000:  111  0    16   32   239  190  173  222  239  190  173  222  239  190  173  222
0x00000010:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000020:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000030:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000040:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000050:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000060:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
0x00000070:  239  190  173  222  239  190  173  222  239  190  173  222  239  190  173  222
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000000 (0) => 0x2010006f (537919599) - 25241 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x2010006f (537919599) - 25578 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x2010006f (537919599) - 25574 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x2010006f (537919599) - 25522 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x2010006f (537919599) - 25587 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x2010006f (537919599) - 25556 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x2010006f (537919599) - 25365 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x2010006f (537919599) - 25583 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x2010006f (537919599) - 25639 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x2010006f (537919599) - 25605 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  004000bb  55555575  5555d555  55555555
0x00000010:  55555555  55557555  55555555  55555555
0x00000020:  fefff5d5  f5575f55  3f6f555d  fe677555
0x00000030:  55517555  bef5bf51  f5f7f5ef  bf915ff5
```






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


### Examples

List predefined debug bus signals
```
debug-bus list-names
```
Output:
```
['brisc_pc', 'trisc0_pc', 'trisc1_pc', 'trisc2_pc', 'ncrisc_pc']
```
Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
```
debug-bus trisc0_pc,trisc1_pc
```
Output:
```
device:0 loc:0,0  trisc0_pc: 0x6000
device:0 loc:0,0  trisc1_pc: 0xa000
```
Prints custom debug bus signal and trisc2_pc
```
debug-bus [7,0,12,0x3ffffff],trisc2_pc
```
Output:
```
device:0 loc:0,0  Debug Bus Config(Diasy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff) = 0x6000
device:0 loc:0,0  trisc2_pc: 0xe000
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






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
  #0 0x00000C4C in main () at /localdev/vjovanovic/tt-exalens/ttexalens/riscv-src/sample.cc 46:22
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
