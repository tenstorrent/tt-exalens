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
00  ----  R---  ----  ----  ----  ----  ----  ----
01  ----  ----  ----  ----  ----  ----  ----  ----
02  ----  ----  ----  ----  ----  ----  ----  ----
03  ----  ----  ----  ----  ----  ----  ----  ----
04  ----  ----  ----  ----  ----  ----  ----  ----
05  ----  ----  ----  ----  ----  ----  ----  ----
06  ----  ----  ----  ----  ----  ----  ----  ----
07  ----  ----  ----  ----  ----  ----  ----  ----
08  ----  ----  ----  ----  ----  ----  ----  ----
09  ----  ----  ----  ----  ----  ----  ----  ----
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
01  dram  ----  R---  ----  ----  dram  ----  ----  ----  ----
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
09  1-11  2-11  3-11  4-11  6-11  7-11  8-11  9-11
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
11  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
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
02  dram  ----  ----  ----  R---  ----  ----  ----  ----  dram
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
11  dram  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functional_wor...
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






## reg

### Usage

```
tensix-reg <register> [--type <data-type>] [ --write <value> ] [ -d <device> ] [ -l <loc> ]
tensix-reg --search <register_pattern> [ --max <max-regs> ] [ -d <device> ] [ -l <loc> ]
```


### Description

Prints/writes to the specified register, at the specified location and device.


### Arguments

- `<register>`: Register to dump/write to. Format: <reg-type>(<reg-parameters>) or register name. <reg-type> Register type. Options: [cfg, dbg]. <reg-parameters> Register parameters, comma separated integers. For cfg: index,mask,shift. For dbg: address.
- `<register-pattern>`: Register pattern used to print register names that match it. Format: wildcard.


### Options

- `--type` = **\<data-type\>**: Data type of the register. This affects print format. Options: [INT_VALUE, ADDRESS, MASK, FLAGS, TENSIX_DATA_FORMAT]. Default: INT_VALUE.
- `--write` = **\<value\>**: Value to write to the register. If not given, register is dumped instead.
- `--max` = **\<max-regs\>**: Maximum number of register names to print when searching or all for everything. Default: 10.
- `-d` = **\<device\>**: Device ID. Optional. Default: current device.
- `-l` = **\<loc\>**: Core location in X-Y or R,C format. Default: current core.


### Examples

Prints configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25)
```
Output:
```
Value of register ConfigurationRegisterDescription(address=4, mask=503316480, shift=25, data_type=<DATA_TYPE.INT_VALUE: 0>, index=...
5
```
Prints debug register with address 0x54
```
reg dbg(0x54)
```
Output:
```
Value of register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 a...
18
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
Prints names of all reigsters that include word format
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
Value of register ConfigurationRegisterDescription(address=240, mask=15, shift=0, data_type=<DATA_TYPE.TENSIX_DATA_FORMAT: 4>, ind...
TensixDataFormat.Float16_b
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT
```
Output:
```
Value of register ConfigurationRegisterDescription(address=4, mask=503316480, shift=25, data_type=<DATA_TYPE.TENSIX_DATA_FORMAT: 4...
TensixDataFormat.Float16_b
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE
```
Output:
```
Value of register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 a...
18
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18
```
Output:
```
Register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 and locati...
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0
```
Output:
```
Register ConfigurationRegisterDescription(address=4, mask=503316480, shift=25, data_type=<DATA_TYPE.INT_VALUE: 0>, index=1) on dev...
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 a...
18
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 a...
18
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0
```
Output:
```
Value of register DebugRegisterDescription(address=84, mask=4294967295, shift=0, data_type=<DATA_TYPE.INT_VALUE: 0>) on device 0 a...
18
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
Prints all configuration reigsters for device with id 0 and current core
```
cfg -d 0
```
Output:
```
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
└───────────────────┴──────────────────────────┘
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
Prints all configuration registers for current device and core
```
cfg all
```
Output:
```
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
└───────────────────┴──────────────────────────┘
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
cfg unpack
```
Output:
```
Configuration registers for location 0,0 on device 0
UNPACKER
┌─────────────────────────┬────────────────────────────┬──────────────────────────┐   ┌────────────────────┬──────────────────────...
│ UNPACK CONFIG           │ REG_ID = 1                 │ REG_ID = 2               │   │ TILE DESCRIPTOR    │ REG_ID = 1           ...
├─────────────────────────┼────────────────────────────┼──────────────────────────┤   ├────────────────────┼──────────────────────...
│ out_data_format         │ TensixDataFormat.Float16_b │ TensixDataFormat.Float32 │   │ in_data_format     │ TensixDataFormat.Floa...
│ throttle_mode           │ 0                          │ 0                        │   │ uncompressed       │ False                ...
│ context_count           │ 0                          │ 0                        │   │ reserved_0         │ 0                    ...
│ haloize_mode            │ 0                          │ 0                        │   │ blobs_per_xy_plane │ 0                    ...
│ tileize_mode            │ 0                          │ 0                        │   │ reserved_1         │ 0                    ...
│ unpack_src_reg_set_upd  │ False                      │ False                    │   │ x_dim              │ 0                    ...
│ unpack_if_sel           │ False                      │ False                    │   │ y_dim              │ 0                    ...
│ upsample_rate           │ 0                          │ 0                        │   │ z_dim              │ 0                    ...
│ reserved_1              │ 0                          │ 0                        │   │ w_dim              │ 0                    ...
│ upsample_and_interleave │ False                      │ False                    │   │ digest_type        │ 0                    ...
│ shift_amount            │ 0                          │ 0                        │   │ digest_size        │ 0                    ...
│ uncompress_cntx0_3      │ 0                          │ 0                        │   │ blobs_y_start      │ 0                    ...
│ unpack_if_sel_cntx0_3   │ 0                          │ 0                        │   └────────────────────┴──────────────────────...
│ force_shared_exp        │ False                      │ False                    │                                               ...
│ reserved_2              │ 0                          │ 0                        │                                               ...
...
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
0x00000050:  19   0   0    0   18   0   0  0  19   0   0    0    19   0   0    0
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
0,0 (L1) : 0x00000000 (0) => 0x2010006f (537919599) - 25290 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x2010006f (537919599) - 25434 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x2010006f (537919599) - 25680 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x2010006f (537919599) - 25652 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x2010006f (537919599) - 25553 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x2010006f (537919599) - 25654 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x2010006f (537919599) - 25304 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x2010006f (537919599) - 25658 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x2010006f (537919599) - 25679 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x2010006f (537919599) - 25641 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  000000bb  55555555  55555575  55515555
0x00000010:  55555555  55555555  55555555  55555555
0x00000020:  777f807f  907f8080  c0907f77  807f8075
0x00000030:  80007580  5f905580  75c07fc0  80c07dc0
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
  #0 0x00000C50 in main () at /localdev/adjordjevic/work/tt-exalens/ttexalens/riscv-src/sample.cc 46:22
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
