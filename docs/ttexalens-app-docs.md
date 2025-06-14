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
0x00000000:  00001234
```
Read 16 words from address 0
```
brxy 0,0 0x0 16
```
Output:
```
0,0 (L1) : 0x00000000 (64 bytes)
0x00000000:  00001234  00001234  00001234  00001234
0x00000010:  00001234  00001234  00001234  00001234
0x00000020:  00001234  00001234  8e2e7c10  f70aa1b3
0x00000030:  00cab470  93d30160  6e8eb36c  abfb37a1
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Output:
```
0,0 (L1) : 0x00000000 (128 bytes)
0x00000000:  52   18   0    0    52  18   0    0    52   18   0    0    52   18   0    0
0x00000010:  52   18   0    0    52  18   0    0    52   18   0    0    52   18   0    0
0x00000020:  52   18   0    0    52  18   0    0    16   124  46   142  179  161  10   247
0x00000030:  112  180  202  0    96  1    211  147  108  179  142  110  161  55   251  171
0x00000040:  107  22   160  255  17  242  88   92   22   116  148  228  28   19   45   73
0x00000050:  82   15   140  152  18  0    0    0    201  139  253  216  184  109  120  125
0x00000060:  74   6    0    228  94  148  44   192  239  149  113  107  0    230  123  216
0x00000070:  79   7    6    34   21  132  10   117  49   209  223  244  194  238  251  6
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Output:
```
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000000 (0) => 0x00001234 (4660) - 22308 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000004 (4) => 0x00001234 (4660) - 22588 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000008 (8) => 0x00001234 (4660) - 22598 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000000c (12) => 0x00001234 (4660) - 22582 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000010 (16) => 0x00001234 (4660) - 22604 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000014 (20) => 0x00001234 (4660) - 22622 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000018 (24) => 0x00001234 (4660) - 22656 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x0000001c (28) => 0x00001234 (4660) - 22588 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000020 (32) => 0x00001234 (4660) - 22610 times
Sampling for 0.15625 seconds...
0,0 (L1) : 0x00000024 (36) => 0x00001234 (4660) - 22577 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```
Output:
```
ch0 (DRAM) : 0x00000000 (64 bytes)
0x00000000:  404000b9  55555555  55555555  55555555
0x00000010:  5555dd55  55555555  51555555  d5557555
0x00000020:  45704554  51755175  55455575  55404140
0x00000030:  51515175  55555554  55705554  51745570
```






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
  #0 0x00000C4C in main () at /localdev/adjordjevic/work/tt-exalens/ttexalens/riscv-src/sample.cc 46:22
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


### Examples

List predefined debug bus signals
```
debug-bus list-names
```
Output:
```
dict_keys(['brisc_pc', 'trisc0_pc', 'trisc1_pc', 'trisc2_pc', 'ncrisc_pc'])
```
Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
```
debug-bus trisc0_pc,trisc1_pc
```
Output:
```
device:0 loc:0,0  trisc0_pc: 0xc491c5c
device:0 loc:0,0  trisc1_pc: 0x33b76695
```
Prints custom debug bus signal and trisc2_pc
```
debug-bus [7,0,12,0x3ffffff],trisc2_pc
```
Output:
```
device:0 loc:0,0  Debug Bus Config(Daisy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff) = 0x491c5c
device:0 loc:0,0  trisc2_pc: 0x227903b8
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
00  R---  ----  ----  ----  ----  ----  ----  ----
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
    security
    l2cpu

==== Device 0
    00           01    02    03    04    05    06    07    08    09
00  dram         eth   eth   eth   eth   dram  eth   eth   eth   eth
01  dram         R---  ----  ----  ----  dram  ----  ----  ----  ----
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
    00           01                  02                  03                  04                  05    06                  07     ...
00  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
01  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
02  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
03  pcie         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
04  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
06  dram         eth                 eth                 eth                 eth                 dram  eth                 eth    ...
07  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
08  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
09  router_only  functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
10  arc          functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
11  dram         harvested_workers   harvested_workers   harvested_workers   harvested_workers   dram  harvested_workers   harvest...
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
    00           01    02    03    04    05    06    07    08    09
00  dram         eth   eth   eth   eth   eth   eth   eth   eth   dram
01  dram         ----  ----  ----  ----  ----  ----  ----  ----  dram
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
05  dram         functional_workers  functional_workers  functional_workers  functional_workers  dram  functional_workers  functio...
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
Prints all configuration registers for device with id 0 and current core
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
│ reserved_2              │ 0                        │ 0                        │                                                 ...
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
15 - a5      0x00000001
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
32 - pc     0x00000c48
Soft reset  0           1         1         1
Halted      False       -         -         -
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]
- `--risc, -r` = **\<risc-id\>**: RiscV ID (0: brisc, 1-3 triscs, all). [default: all]






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
noc register <reg-names> [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
```


### Description

Displays NOC (Network on Chip) registers.
• "noc status" prints status registers for transaction counters.
• "noc all" prints all registers.
• "noc register <reg-names>" prints specific register(s) by name.


### Arguments

- `device-id`: ID of the device [default: current active]
- `noc-id`: Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
- `loc`: Location identifier (e.g. 0-0) [default: current active]
- `reg-names`: Name of specific NOC register(s) to display, can be comma-separated


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
          Transaction Counters (Sent)                        Transaction Counters (Received)
╭────────────────────────────┬────────────────╮ ╭────────────────────────────────┬───────────────────────╮
│ Description                │ Value          │ │ Description                    │ Value                 │
├────────────────────────────┼────────────────┤ ├────────────────────────────────┼───────────────────────┤
│ nonposted write reqs sent  │ 0x00000000 (0) │ │ nonposted write reqs received  │ 0x00008c3a (35898)    │
│ posted write reqs sent     │ 0x00000000 (0) │ │ posted write reqs received     │ 0x00000000 (0)        │
│ nonposted write words sent │ 0x00000000 (0) │ │ nonposted write words received │ 0x00008c3a (35898)    │
│ posted write words sent    │ 0x00000000 (0) │ │ posted write words received    │ 0x00000000 (0)        │
│ write acks received        │ 0x00000000 (0) │ │ write acks sent                │ 0x00008c3a (35898)    │
│ read reqs sent             │ 0x00000000 (0) │ │ read reqs received             │ 0x00a40208 (10748424) │
│ read words received        │ 0x00000000 (0) │ │ read words sent                │ 0x00a40208 (10748424) │
│ read resps received        │ 0x00000000 (0) │ │ read resps sent                │ 0x00a40209 (10748425) │
╰────────────────────────────┴────────────────╯ ╰────────────────────────────────┴───────────────────────╯

NOC1 Status Registers
          Transaction Counters (Sent)                     Transaction Counters (Received)
╭────────────────────────────┬────────────────╮ ╭────────────────────────────────┬─────────────────╮
│ Description                │ Value          │ │ Description                    │ Value           │
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

  nonposted write reqs received    0x00008c3a (35898)
  posted write reqs received       0x00000000 (0)
  nonposted write words received   0x00008c3a (35898)
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
│ NIU_MST_RD_REQ_SENT │ 0x00000000 (0) │
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
╭───────────────────────────────┬────────────────╮
│ Description                   │ Value          │
├───────────────────────────────┼────────────────┤
│ NIU_MST_RD_REQ_SENT           │ 0x00000000 (0) │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0x00000000 (0) │
╰───────────────────────────────┴────────────────╯

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
  HALTED PC=0x00000c50 - BRISC 0,0 [0]
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
Value of register ConfigurationRegisterDescription(address: 0x4, mask: 0x1e000000, shift: 25, native_data_type: DATA_TYPE.INT_VALU...
0
```
Prints debug register with address 0x54
```
reg dbg(0x54)
```
Output:
```
Value of register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on de...
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
Value of register ConfigurationRegisterDescription(address: 0xffef00f0, mask: 0xf, shift: 0, native_data_type: DATA_TYPE.TENSIX_DA...
TensixDataFormat.Float32
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT
```
Output:
```
Value of register ConfigurationRegisterDescription(address: 0x4, mask: 0x1e000000, shift: 25, native_data_type: DATA_TYPE.TENSIX_D...
TensixDataFormat.Float32
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE
```
Output:
```
Value of register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on de...
18
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18
```
Output:
```
Register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on device 0 an...
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0
```
Output:
```
Register ConfigurationRegisterDescription(address: 0x4, mask: 0x1e000000, shift: 25, native_data_type: DATA_TYPE.INT_VALUE, index:...
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on de...
18
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0
```
Output:
```
Value of register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on de...
18
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0
```
Output:
```
Value of register DebugRegisterDescription(address: 0x54, mask: 0xffffffff, shift: 0, native_data_type: DATA_TYPE.INT_VALUE) on de...
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
