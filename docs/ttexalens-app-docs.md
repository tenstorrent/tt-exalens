## burst-read-xy / brxy

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


### Examples

Read 1 word from address 0
```
brxy 0,0 0x0 1                          
```
Output:
```
1-2 (0,0) : 0x00000000 (4 total bytes)
(l1) : 0x00000000 (4 bytes)
0x00000000:  00100073
```
Read 16 words from address 0
```
brxy 0,0 0x0 16                         
```
Output:
```
1-2 (0,0) : 0x00000000 (64 total bytes)
(l1) : 0x00000000 (64 bytes)
0x00000000:  00100073  00100073  00100073  00100073
0x00000010:  00100073  00100073  00100073  00100073
0x00000020:  00100073  00100073  00100073  00100073
0x00000030:  00100073  00100073  00100073  00100073
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8             
```
Output:
```
1-2 (0,0) : 0x00000000 (128 total bytes)
(l1) : 0x00000000 (128 bytes)
0x00000000:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000010:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000020:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000030:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000040:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000050:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000060:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
0x00000070:  115  0  16  0  115  0  16  0  115  0  16  0  115  0  16  0
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5  
```
Output:
```
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000000 (0) => 0x00100073 (1048691) - 21410 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000004 (4) => 0x00100073 (1048691) - 21388 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000008 (8) => 0x00100073 (1048691) - 21589 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x0000000c (12) => 0x00100073 (1048691) - 21559 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000010 (16) => 0x00100073 (1048691) - 21485 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000014 (20) => 0x00100073 (1048691) - 21523 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000018 (24) => 0x00100073 (1048691) - 21626 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x0000001c (28) => 0x00100073 (1048691) - 21670 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000020 (32) => 0x00100073 (1048691) - 21632 times
Sampling for 0.15625 seconds...
1-2 (0,0) (l1) 0x00000024 (36) => 0x00100073 (1048691) - 21603 times
...
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16                         
```
Output:
```
0-0 (d0,0) : 0x00000000 (64 total bytes)
(dram_bank) : 0x00000000 (64 bytes)
0x00000000:  bfac8332  cafeefac  baf9caf9  dab0cab0
0x00000010:  bad0fab0  feedbeef  23deeef1  993f8dca
0x00000020:  bfac8332  cafeefac  baf9caf9  dab0cab0
0x00000030:  bad0fab0  feedbeef  23deeef1  993f8dca
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.






## bt

### Usage

```
callstack <elf-files> [-o <offsets>] [-r <risc>] [-m <max-depth>] [-d <device>] [-l <loc>]
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
File build/riscv-src/wormhole/sample.brisc.elf does not exist
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## debug-bus / dbus

### Usage

```
debug-bus list-signals [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
debug-bus list-groups [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-groups>] [-s]
debug-bus group <group-name> <l1-address> [--samples <num>] [--sampling-interval <cycles>] [--search <pattern>] [--max <max-sigs>] [-d <device>] [-l <loc>] [-s]
debug-bus <signals> [-d <device>] [-l <loc>] [-s]
```


### Description

Commands for RISC-V debugging:
- list-signals:    List all predefined debug bus signal names.
--search:    Search for signals by pattern (wildcard format)
--max:       Limit number of results
- list-groups:   List all debug bus signal groups.
--search:    Search for groups by pattern (wildcard format)
--max:       Limit number of results
- group <group-name> <l1-address>:   List all signals in group using L1 sampling
--search:    Search for signals by pattern (wildcard format)
--samples:   Number of samples
--sampling-interval: Delay between samples
<l1-address>:      Byte address in L1 memory for L1 sampling mode (must be 16-byte aligned).
Enables L1 sampling: signal(s) are captured as 128-bit words to L1 memory at the given address
instead of direct 32-bit register read. Each sample uses 16 bytes. All samples must fit in the first 1 MiB (0x0 - 0xFFFFF).
- [<signals>]:   List of signals described by signal name or signal description.
<signal-description>: {DaisyId,RDSel,SigSel,Mask}
- DaisyId   - daisy chain identifier
- RDSel     - select 32bit data in 128bit register (values 0-3)
- SigSel    - select 128bit register
- Mask      - 32bit mask for significant bits (optional)


### Options

- `-s,` = **--simple**: Print simple output.
- `--search` = **\<pattern\>**: Search for signals by pattern (in wildcard format).
- `--max` = **\<max-sigs\>**: Limit --search output (default: 10, use --max "all" to print all matches). [default: 10].
- `--samples` = **\<num\>**: (L1 sampling only) Number of 128-bit samples to capture. [default: 1]
- `--sampling-interval` = **\<cycles\>**: (L1 sampling only, if --samples > 1) Delay in clock cycles between samples. Must be 2-256.[ default: 2]


### Examples

List up to 10 predefined debug bus signals (default max)
```
debug-bus list-signals                                        
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0)
                                 Signals                                 
╭──────────────────────────┬────────────────────────────────────┬───────╮
│ Group                    │ Name                               │ Value │
├──────────────────────────┼────────────────────────────────────┼───────┤
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_w_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_w_cr      │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_cr/0    │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_x_cr/1    │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_y_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_y_cr      │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_z_counter │ 0x0   │
│ adcs0_unpacker0_channel0 │ adcs0_unpacker0_channel0_z_cr      │ 0x0   │
│ adcs0_unpacker0_channel1 │ adcs0_unpacker0_channel1_w_counter │ 0x0   │
╰──────────────────────────┴────────────────────────────────────┴───────╯

```
List all predefined debug bus signals
```
debug-bus list-signals --max all                              
```
Output:
```
=== Device 0 - location 0,0)
                                                                  Signals                                                         ...
╭─────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┬────...
│ Group                                       │ Name                                                                         │ Val...
├─────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────...
│                                             │ adcs_i_pack_req_dest_ds_mask/0                                               │ 0xb...
│                                             │ adcs_i_pack_req_dest_ds_mask/1                                               │ 0xb...
│                                             │ adcs_i_pack_req_dest_ds_mask/2                                               │ 0x6...
│                                             │ l1_addr_core_p15/0                                                           │ 0x1...
│                                             │ l1_addr_core_p15/1                                                           │ 0xc...
│                                             │ l1_addr_core_p23/0                                                           │ Tru...
│                                             │ l1_addr_core_p23/1                                                           │ 0x3...
│                                             │ l1_addr_core_p30/0                                                           │ 0x2...
│                                             │ l1_addr_core_p30/1                                                           │ 0x5...
│                                             │ l1_addr_core_p38/0                                                           │ 0x3...
│                                             │ l1_addr_core_p38/1                                                           │ 0x3...
│                                             │ packed_data_p5/0                                                             │ 0x5...
│                                             │ packed_data_p5/1                                                             │ 0xb...
│                                             │ packed_data_p5/2                                                             │ 0x2...
│                                             │ rwc_i_dest_target_reg_cfg_math_offset/0                                      │ 0x0...
...
```
List up to 5 signals whose names contain 'pc'
```
debug-bus list-signals --search *pc* --max 5                  
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0)
                      Signals                       
╭────────────────┬───────────────────────┬─────────╮
│ Group          │ Name                  │ Value   │
├────────────────┼───────────────────────┼─────────┤
│ brisc_group_a  │ brisc_dbg_obs_cmt_pc  │ 0x0     │
│ brisc_group_b  │ brisc_id_ex_pc        │ 0x8     │
│ brisc_group_b  │ brisc_pc              │ 0x8     │
│ ncrisc_group_a │ ncrisc_dbg_obs_cmt_pc │ 0x48164 │
│ ncrisc_group_b │ ncrisc_id_ex_pc       │ 0x48168 │
╰────────────────┴───────────────────────┴─────────╯

```
List all debug bus signal groups
```
debug-bus list-groups                                         
```
Output:
```
There are matches remaining. To see more results, increase the --max value.
=== Device 0 - location 0,0 - Signal Groups ===
            Groups             
╭─────────────────────────────╮
│ Group Name                  │
├─────────────────────────────┤
│ adcs0_unpacker0_channel0    │
│ adcs0_unpacker0_channel1    │
│ adcs0_unpacker1_channel0    │
│ adcs0_unpacker1_channel1    │
│ adcs2_packers_channel0      │
│ adcs2_packers_channel1      │
│ adcs_dest_fpu_instr_signals │
│ adcs_dest_pack_fifo_signals │
│ adcs_i_pack_req_signals     │
│ adcs_sfpu_dbg_signals       │
╰─────────────────────────────╯

```
List groups whose names match pattern 'brisc'
```
debug-bus list-groups --search brisc*                         
```
Output:
```
=== Device 0 - location 0,0 - Signal Groups ===
     Groups      
╭───────────────╮
│ Group Name    │
├───────────────┤
│ brisc_group_a │
│ brisc_group_b │
│ brisc_group_c │
╰───────────────╯

```
List all signals in group 'brisc_group_a' using L1 sampling, 4 samples, 10 cycles interval
```
debug-bus group brisc_group_a 0x1000 --samples 4 --sampling-interval 10 
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a ===
                          brisc_group_a                          
╭────────────────────────┬──────────────────────────────────────╮
│ Name                   │ Value                                │
├────────────────────────┼──────────────────────────────────────┤
│ brisc_dbg_obs_cmt_pc   │ [0x0, 0x0, 0x0, 0x0]                 │
│ brisc_dbg_obs_cmt_vld  │ [False, False, False, False]         │
│ brisc_dbg_obs_mem_addr │ [0x10000, 0x10000, 0x10000, 0x10000] │
│ brisc_dbg_obs_mem_rden │ [False, False, False, False]         │
│ brisc_dbg_obs_mem_wren │ [False, False, False, False]         │
│ brisc_i_instrn         │ [0x0, 0x0, 0x0, 0x0]                 │
│ brisc_i_instrn_req_rtr │ [True, True, True, True]             │
│ brisc_i_instrn_vld     │ [False, False, False, False]         │
│ brisc_o_instrn_addr    │ [0x0, 0x0, 0x0, 0x0]                 │
│ brisc_o_instrn_req     │ [False, False, False, False]         │
╰────────────────────────┴──────────────────────────────────────╯

```
List all signals in group 'brisc_group_a' that ends with 'pc' using L1 sampling
```
debug-bus group brisc_group_a 0x1000 --search *pc             
```
Output:
```
=== Device 0 - location 0,0 - Group: brisc_group_a ===
         brisc_group_a          
╭──────────────────────┬───────╮
│ Name                 │ Value │
├──────────────────────┼───────┤
│ brisc_dbg_obs_cmt_pc │ 0x0   │
╰──────────────────────┴───────╯

```
Print values for trisc0_pc and trisc1_pc
```
debug-bus trisc0_pc,trisc1_pc                                 
```
Output:
```
device:0 loc:1-2 (0,0)  trisc0_pc: 0x6008
device:0 loc:1-2 (0,0)  trisc1_pc: 0xa000
```
Print value for a custom signal and trisc2_pc
```
debug-bus {7,0,12,0x3ffffff},trisc2_pc                        
```
Output:
```
device:0 loc:1-2 (0,0)  Daisy:7; Rd Sel:0; Sig Sel:12; Mask:0x3ffffff: 0x0
device:0 loc:1-2 (0,0)  trisc2_pc: 0xe000
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


### Options

- `-d` = **\<device-id\>**: ID of the device [default: all]
- `axis-coordinate`: Coordinate system for the axis [default: logical-tensix] Supported: noc0, noc1, translated, die, logical-tensix, logical-eth, logical-dram
- `cell-contents`: A comma separated list of the cell contents [default: riscv] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset), or block type if there are no RISC-V cores block - show the type of the block at that coordinate logical, noc0, noc1, translated, die - show coordinate noc0_id - show the NOC0 node ID (x-y) for the block noc1_id - show the NOC1 node ID (x-y) for the block


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

==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00     01     02     03     04     05     06     07     08     09     10     11     12     13
00  ----R  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
01  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
02  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
03  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
04  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
05  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
06  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
07  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
08  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
09  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----  -----
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
    harvested_eth
    arc
    dram
    harvested_dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00  01           02     03           04           05             06           07           08           09  10           11   ...
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

==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00    01    02    03    04    05    06    07     08     09     10     11     12     13
00  1-2   2-2   3-2   4-2   5-2   6-2   7-2   10-2   11-2   12-2   13-2   14-2   15-2   16-2
01  1-3   2-3   3-3   4-3   5-3   6-3   7-3   10-3   11-3   12-3   13-3   14-3   15-3   16-3
02  1-4   2-4   3-4   4-4   5-4   6-4   7-4   10-4   11-4   12-4   13-4   14-4   15-4   16-4
03  1-5   2-5   3-5   4-5   5-5   6-5   7-5   10-5   11-5   12-5   13-5   14-5   15-5   16-5
04  1-6   2-6   3-6   4-6   5-6   6-6   7-6   10-6   11-6   12-6   13-6   14-6   15-6   16-6
05  1-7   2-7   3-7   4-7   5-7   6-7   7-7   10-7   11-7   12-7   13-7   14-7   15-7   16-7
06  1-8   2-8   3-8   4-8   5-8   6-8   7-8   10-8   11-8   12-8   13-8   14-8   15-8   16-8
07  1-9   2-9   3-9   4-9   5-9   6-9   7-9   10-9   11-9   12-9   13-9   14-9   15-9   16-9
08  1-10  2-10  3-10  4-10  5-10  6-10  7-10  10-10  11-10  12-10  13-10  14-10  15-10  16-10
09  1-11  2-11  3-11  4-11  5-11  6-11  7-11  10-11  11-11  12-11  13-11  14-11  15-11  16-11
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend       
```
Output:
```
==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00    01                  02                  03                  04                  05                  06                  ...
00  dram  router_only         pcie                router_only         router_only         router_only         router_only         ...
01  dram  eth                 eth                 eth                 eth                 harvested_eth       eth                 ...
02  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
03  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
04  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
05  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
06  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
07  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
08  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
09  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
10  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
11  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
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
    harvested_eth
    arc
    dram
    harvested_dram
    pcie
    router_only
    harvested_workers
    security
    l2cpu

==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00  01           02           03     04           05           06             07           08           09             10     ...
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

==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00    01    02   03   04    05    06   07
00  0-0   0-2   0-9  0-5  9-0   9-2   9-9  9-5
01  0-1   0-10  0-4  0-7  9-1   9-10  9-4  9-7
02  0-11  0-3   0-8  0-6  9-11  9-3   9-8  9-6
```
Shows the block type on noc0 axis for device 0 without legend
```
device -d 0 noc0 block --no-legend  
```
Output:
```
==== Device 0 [p150 / local] (Unique ID: 0x58506e131fe32c7b)
    00    01                  02                  03                  04                  05                  06                  ...
00  dram  router_only         pcie                router_only         router_only         router_only         router_only         ...
01  dram  eth                 eth                 eth                 eth                 harvested_eth       eth                 ...
02  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
03  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
04  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
05  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
06  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
07  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
08  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
09  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
10  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
11  dram  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  functional_workers  ...
```






## tensix

### Usage

```
dump-tensix-state [ <group> ] [ -d <device> ] [ -l <loc> ] [ -v ] [ -t <thread-id> ] [ -a <l1-address> ]
```


### Description

Prints the tensix state group of the given name, at the specified location and device.


### Options

- `group`: Tensix state group to dump. Options: [all, alu, pack, unpack, gpr, rwc, adc]
- `-t` = **\<thread-id\>**: Thread ID. Options: [0, 1, 2] Default: all (only for gpr group)
- `-a` = **\<l1-address\>**: L1 address to save group data. Only used for RWC and ADC groups.


### Examples

Prints tensix state for current device and core
```
tensix              
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core using L1 address 0x0 for RWC and ADC groups
```
tensix -a 0x0       
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for device with id 0 and current core
```
tensix -d 0         
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core at location 0,0
```
tensix -l 0,0       
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints tensix state for current device and core
```
tensix all          
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
...
```
Prints alu configuration registers for current device and core
```
tensix alu          
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ Format_Dstacc     │ TensixDataFormat.Int8    │
│ Fp32_enabled      │ False                    │
│ SFPU_Fp32_enabled │ False                    │
│ INT8_math_enabled │ False                    │
└───────────────────┴──────────────────────────┘
```
Prints packer's configuration registers for current device and core
```
tensix pack         
```
Output:
```
Tensix registers for location 0,0 on device 0
PACKER
┌──────────────────────────┬──────────┐
│ COUNTERS                 │ VALUES   │
├──────────────────────────┼──────────┤
│ pack_per_xy_plane        │ 0        │
│ pack_reads_per_xy_plane  │ 0        │
│ pack_xys_per_til         │ 0        │
│ pack_yz_transposed       │ False    │
│ pack_per_xy_plane_offset │ 0        │
└──────────────────────────┴──────────┘
┌─────────────────────────────────────┬──────────────────────────┐
│ PACK CONFIG                         │ VALUES                   │
├─────────────────────────────────────┼──────────────────────────┤
│ row_ptr_section_size                │ 0                        │
│ exp_section_size                    │ 0                        │
│ l1_dest_addr                        │ 0x0                      │
│ uncompress                          │ False                    │
│ add_l1_dest_addr_offset             │ False                    │
│ disable_pack_zero_flag              │ False                    │
...
```
Prints unpacker's configuration registers for current device and core
```
tensix unpack       
```
Output:
```
Tensix registers for location 0,0 on device 0
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
│ upsample_and_interleave │ False                    │ False                    │   │ blobs_y_start      │ 0                      ...
│ shift_amount            │ 0                        │ 0                        │   │ digest_type        │ 0                      ...
│ uncompress_cntx0_3      │ 0                        │ 0                        │   │ digest_size        │ 0                      ...
│ unpack_if_sel_cntx0_3   │ 0                        │ 0                        │   └────────────────────┴────────────────────────...
│ force_shared_exp        │ False                    │ False                    │                                                 ...
│ reserved_2              │ 0                        │ 0                        │                                                 ...
...
```
Prints general purpose registers for current device and core
```
tensix gpr          
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐   ┌─────────────────────┬───────────...
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │   │ Thread 2            │ Values    ...
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤   ├─────────────────────┼───────────...
│ zero                        │ 2051754816      │   │ zero                     │ 776945704  │   │ zero                │ 2477508864...
│ dbg_reserved                │ 1152047138      │   │ dbg_reserved             │ 1220256607 │   │ dbg_reserved        │ 2952796309...
│ dbg_msg                     │ 2523032536      │   │ dbg_msg                  │ 839413818  │   │ dbg_msg             │ 1711037497...
│ dbg_ckid                    │ 3557268800      │   │ dbg_ckid                 │ 662869548  │   │ dbg_ckid            │ 4216899268...
│ operand_base_addr           │ 0x2b66a51c      │   │ perf_dbus_cntl           │ 3093930048 │   │ dest_offset_lo      │ 79862278  ...
│ operand_offset_addr         │ 0xc880f018      │   │ perf_mem_dump_cntl_clear │ 1084998744 │   │ gpr_5               │ 482687064 ...
│ gpr_6                       │ 2016645801      │   │ perf_mem_dump_cntl_set   │ 3410074433 │   │ gpr_6               │ 933765698 ...
│ gpr_7                       │ 1410007695      │   │ perf_cnt_start           │ 2498889496 │   │ gpr_7               │ 4061307904...
│ zero_0                      │ 1254655820      │   │ perf_cnt_stop            │ 4201620465 │   │ dest_offset_hi      │ 3951389968...
│ zero_1                      │ 153192072       │   │ perf_epoch_base_addr     │ 0xf85ee932 │   │ gpr_9               │ 1562665222...
│ zero_2                      │ 1115993518      │   │ perf_epoch_offset        │ 3625095708 │   │ gpr_10              │ 3295979804...
│ zero_3                      │ 1081757019      │   │ gpr_11                   │ 2192739596 │   │ gpr_11              │ 1745175840...
│ tmp0                        │ 1497379780      │   │ gpr_12                   │ 1971383056 │   │ output_addr         │ 0x80a58ee7...
│ tmp1                        │ 2298493695      │   │ gpr_13                   │ 699494416  │   │ gpr_13              │ 2944993464...
│ tile_size                   │ 1879157888      │   │ gpr_14                   │ 305871507  │   │ gpr_14              │ 244351402 ...
...
```
Prints all general purpose registers for current device and core
```
tensix gpr -v       
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐   ┌─────────────────────┬───────────...
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │   │ Thread 2            │ Values    ...
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤   ├─────────────────────┼───────────...
│ zero                        │ 2051754816      │   │ zero                     │ 776945704  │   │ zero                │ 2477508864...
│ dbg_reserved                │ 1152047138      │   │ dbg_reserved             │ 1220256607 │   │ dbg_reserved        │ 2952796309...
│ dbg_msg                     │ 2523032536      │   │ dbg_msg                  │ 839413818  │   │ dbg_msg             │ 1711037497...
│ dbg_ckid                    │ 3557268800      │   │ dbg_ckid                 │ 662869548  │   │ dbg_ckid            │ 4216899268...
│ operand_base_addr           │ 0x2b66a51c      │   │ perf_dbus_cntl           │ 3093930048 │   │ dest_offset_lo      │ 79862278  ...
│ operand_offset_addr         │ 0xc880f018      │   │ perf_mem_dump_cntl_clear │ 1084998744 │   │ gpr_5               │ 482687064 ...
│ gpr_6                       │ 2016645801      │   │ perf_mem_dump_cntl_set   │ 3410074433 │   │ gpr_6               │ 933765698 ...
│ gpr_7                       │ 1410007695      │   │ perf_cnt_start           │ 2498889496 │   │ gpr_7               │ 4061307904...
│ zero_0                      │ 1254655820      │   │ perf_cnt_stop            │ 4201620465 │   │ dest_offset_hi      │ 3951389968...
│ zero_1                      │ 153192072       │   │ perf_epoch_base_addr     │ 0xf85ee932 │   │ gpr_9               │ 1562665222...
│ zero_2                      │ 1115993518      │   │ perf_epoch_offset        │ 3625095708 │   │ gpr_10              │ 3295979804...
│ zero_3                      │ 1081757019      │   │ gpr_11                   │ 2192739596 │   │ gpr_11              │ 1745175840...
│ tmp0                        │ 1497379780      │   │ gpr_12                   │ 1971383056 │   │ output_addr         │ 0x80a58ee7...
│ tmp1                        │ 2298493695      │   │ gpr_13                   │ 699494416  │   │ gpr_13              │ 2944993464...
│ tile_size                   │ 1879157888      │   │ gpr_14                   │ 305871507  │   │ gpr_14              │ 244351402 ...
...
```
Prints general purpose registers for threads 0 and 1 for current device and core
```
tensix gpr -t 0,1   
```
Output:
```
Tensix registers for location 0,0 on device 0
GPR
┌─────────────────────────────┬─────────────────┐   ┌──────────────────────────┬────────────┐
│ Thread 0                    │ Values          │   │ Thread 1                 │ Values     │
├─────────────────────────────┼─────────────────┤   ├──────────────────────────┼────────────┤
│ zero                        │ 2051754816      │   │ zero                     │ 776945704  │
│ dbg_reserved                │ 1152047138      │   │ dbg_reserved             │ 1220256607 │
│ dbg_msg                     │ 2523032536      │   │ dbg_msg                  │ 839413818  │
│ dbg_ckid                    │ 3557268800      │   │ dbg_ckid                 │ 662869548  │
│ operand_base_addr           │ 0x2b66a51c      │   │ perf_dbus_cntl           │ 3093930048 │
│ operand_offset_addr         │ 0xc880f018      │   │ perf_mem_dump_cntl_clear │ 1084998744 │
│ gpr_6                       │ 2016645801      │   │ perf_mem_dump_cntl_set   │ 3410074433 │
│ gpr_7                       │ 1410007695      │   │ perf_cnt_start           │ 2498889496 │
│ zero_0                      │ 1254655820      │   │ perf_cnt_stop            │ 4201620465 │
│ zero_1                      │ 153192072       │   │ perf_epoch_base_addr     │ 0xf85ee932 │
│ zero_2                      │ 1115993518      │   │ perf_epoch_offset        │ 3625095708 │
│ zero_3                      │ 1081757019      │   │ gpr_11                   │ 2192739596 │
│ tmp0                        │ 1497379780      │   │ gpr_12                   │ 1971383056 │
│ tmp1                        │ 2298493695      │   │ gpr_13                   │ 699494416  │
│ tile_size                   │ 1879157888      │   │ gpr_14                   │ 305871507  │
...
```
Prints RWC group for current device and core
```
tensix rwc          
```
Output:
```
Tensix registers for location 0,0 on device 0
RWCs
┌─────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌─────────────────┬──────────┐
│ COORDINATES_A   │ Values   │   │ CONTROL_SIGNALS          │ Values   │   │ COORDINATES_B   │ Values   │
├─────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├─────────────────┼──────────┤
│ rwc0_dst        │ 0xf      │   │ i_thread_state_id        │ 0x0      │   │ rwc2_dst_cr     │ 0xf      │
│ rwc2_srcb_cr    │ 0x0      │   │ i_opcode[23..16]         │ 0x0      │   │ rwc2_dst        │ 0xf      │
│ rwc2_srcb       │ 0xf      │   │ i_instrn_payload[54..48] │ 0x0      │   │ rwc1_dst_cr     │ 0xf      │
│ rwc1_srcb_cr    │ 0x3c     │   │ i_instrn_payload[71..55] │ 0x0      │   │ rwc1_dst        │ 0xf      │
│ rwc1_srcb       │ 0xf      │   │ i_opcode[15..8]          │ 0x0      │   │ rwc0_dst_cr     │ 0xf      │
│ rwc0_srcb_cr    │ 0x3      │   │ i_instrn_payload[30..24] │ 0x0      │   │ rwc0_dst        │ 0xf      │
│ rwc0_srcb       │ 0xf      │   │ i_instrn_payload[47..31] │ 0x0      │   └─────────────────┴──────────┘
│ rwc2_srca_cr    │ 0x0      │   │ i_opcode[8]              │ 0x0      │                                 
│ rwc2_srca       │ 0xf      │   │ i_instrn_payload[23..0]  │ 0x0      │                                 
│ rwc1_srca_cr    │ 0x3c     │   └──────────────────────────┴──────────┘                                 
│ rwc1_srca       │ 0xf      │                                                                           
│ rwc0_srca_cr    │ 0x3      │                                                                           
│ rwc0_srca       │ 0xf      │                                                                           
└─────────────────┴──────────┘                                                                           
┌───────────────────────────────────────────┬──────────┐   ┌───────────────────────────┬──────────┐   ┌───────────────────────────...
...
```
Prints RWC group for current device and core using L1 address 0x0
```
tensix rwc -a 0x0   
```
Output:
```
Tensix registers for location 0,0 on device 0
RWCs
┌─────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌─────────────────┬──────────┐
│ COORDINATES_A   │ Values   │   │ CONTROL_SIGNALS          │ Values   │   │ COORDINATES_B   │ Values   │
├─────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├─────────────────┼──────────┤
│ rwc0_dst        │ 0xf      │   │ i_thread_state_id        │ 0x0      │   │ rwc2_dst_cr     │ 0xf      │
│ rwc2_srcb_cr    │ 0x0      │   │ i_opcode[23..16]         │ 0x0      │   │ rwc2_dst        │ 0xf      │
│ rwc2_srcb       │ 0xf      │   │ i_instrn_payload[54..48] │ 0x0      │   │ rwc1_dst_cr     │ 0xf      │
│ rwc1_srcb_cr    │ 0x3c     │   │ i_instrn_payload[71..55] │ 0x0      │   │ rwc1_dst        │ 0xf      │
│ rwc1_srcb       │ 0xf      │   │ i_opcode[15..8]          │ 0x0      │   │ rwc0_dst_cr     │ 0xf      │
│ rwc0_srcb_cr    │ 0x3      │   │ i_instrn_payload[30..24] │ 0x0      │   │ rwc0_dst        │ 0xf      │
│ rwc0_srcb       │ 0xf      │   │ i_instrn_payload[47..31] │ 0x0      │   └─────────────────┴──────────┘
│ rwc2_srca_cr    │ 0x0      │   │ i_opcode[8]              │ 0x0      │                                 
│ rwc2_srca       │ 0xf      │   │ i_instrn_payload[23..0]  │ 0x0      │                                 
│ rwc1_srca_cr    │ 0x3c     │   └──────────────────────────┴──────────┘                                 
│ rwc1_srca       │ 0xf      │                                                                           
│ rwc0_srca_cr    │ 0x3      │                                                                           
│ rwc0_srca       │ 0xf      │                                                                           
└─────────────────┴──────────┘                                                                           
┌───────────────────────────────────────────┬──────────┐   ┌───────────────────────────┬──────────┐   ┌───────────────────────────...
...
```
Prints ADC group for current device and core
```
tensix adc          
```
Output:
```
Tensix registers for location 0,0 on device 0
ADCs
No L1 address provided. Disabling atomic group reading for ADC group. Use -a option to specify L1 address.
┌──────────────────────────────┬────────────────────┐   ┌─────────────────────────────────────┬──────────┐   ┌────────────────────...
│ ADCS_I_PACK_REQ_SIGNALS      │ Values             │   │ ADCS_DEST_FPU_INSTR_SIGNALS         │ Values   │   │ ADCS_SFPU_DBG_SIGNA...
├──────────────────────────────┼────────────────────┤   ├─────────────────────────────────────┼──────────┤   ├────────────────────...
│ adcs_i_packer_z_pos          │ 0x3cf3cf           │   │ adcs_dec_instr_single_output_row    │ 0x0      │   │ adcs_dbg_dest_sfpu_...
│ adcs_i_packer_edge_mask      │ 0x6b7a93eea1c69635 │   │ adcs_curr_issue_instr_dest_fpu_addr │ 0x3d6    │   └────────────────────...
│ adcs_i_packer_edge_mask_mode │ 0x0                │   └─────────────────────────────────────┴──────────┘                        ...
└──────────────────────────────┴────────────────────┘                                                                             ...
┌───────────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐
│ ADCS_DEST_PACK_FIFO_SIGNALS   │ Values   │   │ ADCS2_PACKERS_CHANNEL1   │ Values   │   │ ADCS2_PACKERS_CHANNEL0   │ Values   │
├───────────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤
│ adcs_dest_wrmask              │ 0x4      │   │ w_cr                     │ 0x0      │   │ w_cr                     │ 0x0      │
│ adcs_dest_fpu_wr_en           │ 0x0      │   │ w_counter                │ 0x0      │   │ w_counter                │ 0x0      │
│ adcs_dest_fpu_rd_en           │ 0x0      │   │ z_cr                     │ 0x0      │   │ z_cr                     │ 0x0      │
│ adcs_pack_req_fifo_wren       │ 0x0      │   │ z_counter                │ 0x0      │   │ z_counter                │ 0x0      │
│ adcs_pack_req_fifo_rden       │ 0x0      │   │ y_cr                     │ 0x0      │   │ y_cr                     │ 0x0      │
│ adcs_pack_req_fifo_empty      │ 0x1      │   │ y_counter                │ 0x0      │   │ y_counter                │ 0x0      │
│ adcs_pack_req_fifo_full       │ 0x0      │   │ x_cr                     │ 0x0      │   │ x_cr                     │ 0x0      │
...
```
Prints ADC group for current device and core using L1 address 0x0
```
tensix adc -a 0x0   
```
Output:
```
Tensix registers for location 0,0 on device 0
ADCs
┌──────────────────────────────┬────────────────────┐   ┌─────────────────────────────────────┬──────────┐   ┌────────────────────...
│ ADCS_I_PACK_REQ_SIGNALS      │ Values             │   │ ADCS_DEST_FPU_INSTR_SIGNALS         │ Values   │   │ ADCS_SFPU_DBG_SIGNA...
├──────────────────────────────┼────────────────────┤   ├─────────────────────────────────────┼──────────┤   ├────────────────────...
│ adcs_i_packer_z_pos          │ 0x3cf3cf           │   │ adcs_dec_instr_single_output_row    │ 0x0      │   │ adcs_dbg_dest_sfpu_...
│ adcs_i_packer_edge_mask      │ 0x6b7a93eea1c69635 │   │ adcs_curr_issue_instr_dest_fpu_addr │ 0x3d6    │   └────────────────────...
│ adcs_i_packer_edge_mask_mode │ 0x0                │   └─────────────────────────────────────┴──────────┘                        ...
└──────────────────────────────┴────────────────────┘                                                                             ...
┌───────────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐   ┌──────────────────────────┬──────────┐
│ ADCS_DEST_PACK_FIFO_SIGNALS   │ Values   │   │ ADCS2_PACKERS_CHANNEL1   │ Values   │   │ ADCS2_PACKERS_CHANNEL0   │ Values   │
├───────────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤   ├──────────────────────────┼──────────┤
│ adcs_dest_wrmask              │ 0x4      │   │ w_cr                     │ 0x0      │   │ w_cr                     │ 0x0      │
│ adcs_dest_fpu_wr_en           │ 0x0      │   │ w_counter                │ 0x0      │   │ w_counter                │ 0x0      │
│ adcs_dest_fpu_rd_en           │ 0x0      │   │ z_cr                     │ 0x0      │   │ z_cr                     │ 0x0      │
│ adcs_pack_req_fifo_wren       │ 0x0      │   │ z_counter                │ 0x0      │   │ z_counter                │ 0x0      │
│ adcs_pack_req_fifo_rden       │ 0x0      │   │ y_cr                     │ 0x0      │   │ y_cr                     │ 0x0      │
│ adcs_pack_req_fifo_empty      │ 0x1      │   │ y_counter                │ 0x0      │   │ y_counter                │ 0x0      │
│ adcs_pack_req_fifo_full       │ 0x0      │   │ x_cr                     │ 0x0      │   │ x_cr                     │ 0x0      │
└───────────────────────────────┴──────────┘   │ x_counter                │ 0x0      │   │ x_counter                │ 0x0      │
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--verbose, -v`: Execute command with verbose output. [default: False]






## dump-coverage / cov

### Usage

```
dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]
```


### Description

Get coverage data for a given ELF. Extract the gcda from the given core
and place it into the output directory along with its gcno.


### Arguments

- `elf`: Path to the currently running ELF
- `gcda_path`: Output path for the gcda
- `gcno_copy_path`: Optional path to copy the gcno file


### Examples

Pre-requisite: we have to run the elf before running coverage
```
re build/riscv-src/wormhole/cov_test.coverage.brisc.elf -r brisc 
```
Command:
```
cov build/riscv-src/wormhole/cov_test.coverage.brisc.elf cov_test.gcda cov_test.gcno
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## dump-gpr / gpr

### Usage

```
gpr [ <reg-list> ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]
```


### Description

Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
If the core cannot be halted, it prints nothing. If core is not active, an exception
is thrown.


### Options

- `reg-list`: List of registers to dump, comma-separated


### Examples

Command:
```
gpr
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register     brisc       trisc0    trisc1    trisc2    ncrisc
-----------  ----------  --------  --------  --------  --------
0 - zero     0x00000000
1 - ra       0x00000160
2 - sp       0xffb00ff0
3 - gp       0x00008800
4 - tp       0x00000000
5 - t0       0x00000001
6 - t1       0x00020000
7 - t2       0x00000008
8 - s0 / fp  0x00000000
9 - s1       0x00000000
10 - a0      0xffb00fcc
11 - a1      0x00000000
12 - a2      0x00000001
13 - a3      0x00000000
14 - a4      0x00000000
15 - a5      0x00000104
16 - a6      0x00000006
...
```
Command:
```
gpr ra,sp,pc
```
Output:
```
RISC-V registers for location 0,0 on device 0
Register    brisc       trisc0    trisc1    trisc2    ncrisc
----------  ----------  --------  --------  --------  --------
1 - ra      0x00000160
2 - sp      0xffb00ff0
32 - pc     0x00000160
Soft reset  False       True      True      True      False
Halted      False       -         -         -         ?
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## gdb

### Usage

```
gdb start [<port>]
gdb stop
```


### Description

Starts or stops gdb server.


### Options

- `port`: Port of the GDB server. If not specified, an available port will be chosen.


### Examples

Command:
```
gdb start
```
Command:
```
gdb start 6767
```
Command:
```
gdb stop
```






## go

### Usage

```
go [-m <mode>] [-n <noc>] [ -d <device> ] [ -l <loc> ]
```


### Description

Sets the current device/location/noc/4B mode.


### Options

- `-m` = **\<mode\>**: Use 4B mode for communication with the device. [0: False, 1: True]
- `-n` = **\<noc\>**: Use NOC1 or NOC0 for communication with the device. [0: NOC0, 1: NOC1]


### Examples

Command:
```
go -m 1 -n 1 -d 0 -l 0,0
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## help / h

### Usage

```
help [--all] [-v] [<command>]
```


### Description

Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.


### Options

- `-v`: If specified, prints verbose documentation.
- `--all`: If specified, prints all commands.


### Examples

Command:
```
help exit
```
Output:
```
Full Name      Short    Description
-------------  -------  -----------------------------------------------------------------------------------
exit           x
                        Description:
                          Exits the program. The optional argument represents the exit code. Defaults to 0.
-------------  -------  -----------------------------------------------------------------------------------
```
Command:
```
help -v exit
```
Output:
```
Full Name      Short    Description
-------------  -------  -----------------------------------------------------------------------------------
exit           x
                        Description:
                          Exits the program. The optional argument represents the exit code. Defaults to 0.
-------------  -------  -----------------------------------------------------------------------------------
```
Command:
```
help --all
```
Output:
```
Full Name          Short    Description
-----------------  -------  ------------------------------------------------------------------------------------------------------...
exit               x        Exits the program. The optional argument represents the exit code. Defaults to 0.
reload             rl       Reloads files in cli_commands directory. Useful for development of commands.
help               h        Prints documentation summary. Use -v for details. If a command name is specified, it prints documentat...
burst-read-xy      brxy     Reads and prints a block of data from address 'addr' at core <core-loc>.
callstack          bt       Prints callstack using provided elf for a given RiscV core.
debug-bus          dbus     Commands for RISC-V debugging:
dump-tensix-state  tensix   Prints the tensix state group of the given name, at the specified location and device.
dump-gpr           gpr      Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
read               r        Reads and prints a block of data from address 'address'.
riscv              rv       Commands for RISC-V debugging:
tensix-reg         reg      Prints/writes to the specified register, at the specified location and device.
write-xy           wxy      Writes data word to address 'addr' at noc0 location x-y of the current chip.
device             d        Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.
dump-coverage      cov      Get coverage data for a given ELF. Extract the gcda from the given core
gdb                gdb      Starts or stops gdb server.
go                 go       Sets the current device/location/noc/4B mode.
noc                nc       Displays NOC (Network on Chip) registers.
run-elf            re       Loads an elf file into a brisc and runs it.
...
```






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

- `noc-id`: Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
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
==== Device 0 - Location: 1-2
NOC0 Status Registers
              Transaction Counters (Sent)                              Transaction Counters (Received)               
╭────────────────────────────┬────────────┬────────────╮ ╭────────────────────────────────┬────────────┬────────────╮
│ Name                       │ Address    │ Value      │ │ Name                           │ Address    │ Value      │
├────────────────────────────┼────────────┼────────────┤ ├────────────────────────────────┼────────────┼────────────┤
│ write acks received        │ 0xffb20204 │ 0x000002a4 │ │ write acks sent                │ 0xffb202c4 │ 0x0340ebd3 │
│ read resps received        │ 0xffb20208 │ 0x00000001 │ │ read resps sent                │ 0xffb202c8 │ 0x00fb474f │
│ read words received        │ 0xffb2020c │ 0x00000009 │ │ read words sent                │ 0xffb202cc │ 0x00fb474d │
│ read reqs sent             │ 0xffb20214 │ 0x00000001 │ │ read reqs received             │ 0xffb202d4 │ 0x00fb474c │
│ nonposted write words sent │ 0xffb20220 │ 0x00029ff8 │ │ nonposted write words received │ 0xffb202e0 │ 0x03414b67 │
│ posted write words sent    │ 0xffb20224 │ 0x00006000 │ │ posted write words received    │ 0xffb202e4 │ 0x00000000 │
│ nonposted write reqs sent  │ 0xffb20228 │ 0x000002a4 │ │ nonposted write reqs received  │ 0xffb202e8 │ 0x0340ebd3 │
│ posted write reqs sent     │ 0xffb2022c │ 0x00000060 │ │ posted write reqs received     │ 0xffb202ec │ 0x00000000 │
╰────────────────────────────┴────────────┴────────────╯ ╰────────────────────────────────┴────────────┴────────────╯

NOC1 Status Registers
              Transaction Counters (Sent)                              Transaction Counters (Received)               
╭────────────────────────────┬────────────┬────────────╮ ╭────────────────────────────────┬────────────┬────────────╮
│ Name                       │ Address    │ Value      │ │ Name                           │ Address    │ Value      │
...
```
Prints status registers with simple output
```
noc status -s                               
```
Output:
```
==== Device 0 - Location: 1-2
NOC0 Status Registers
              Transaction Counters (Sent)               
                                                        
  write acks received          0xffb20204   0x000002a4  
  read resps received          0xffb20208   0x00000001  
  read words received          0xffb2020c   0x00000009  
  read reqs sent               0xffb20214   0x00000001  
  nonposted write words sent   0xffb20220   0x00029ff8  
  posted write words sent      0xffb20224   0x00006000  
  nonposted write reqs sent    0xffb20228   0x000002a4  
  posted write reqs sent       0xffb2022c   0x00000060  
                                                        

              Transaction Counters (Received)               
                                                            
  write acks sent                  0xffb202c4   0x0340ebd3  
  read resps sent                  0xffb202c8   0x00fb478f  
  read words sent                  0xffb202cc   0x00fb478d  
  read reqs received               0xffb202d4   0x00fb478c  
...
```
Prints a specific register value
```
noc register NIU_MST_RD_REQ_SENT            
```
Output:
```
==== Device 0 - Location: 1-2
                 NOC0 Registers                  
╭─────────────────────┬────────────┬────────────╮
│ Name                │ Address    │ Value      │
├─────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_REQ_SENT │ 0xffb20214 │ 0x00000001 │
╰─────────────────────┴────────────┴────────────╯

                 NOC1 Registers                  
╭─────────────────────┬────────────┬────────────╮
│ Name                │ Address    │ Value      │
├─────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_REQ_SENT │ 0xffb30214 │ 0x00000000 │
╰─────────────────────┴────────────┴────────────╯

```
Prints multiple registers
```
noc register NIU_MST_RD_REQ_SENT,NIU_MST_RD_DATA_WORD_RECEIVED  
```
Output:
```
==== Device 0 - Location: 1-2
                      NOC0 Registers                       
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00000009 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x00000001 │
╰───────────────────────────────┴────────────┴────────────╯

                      NOC1 Registers                       
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb3020c │ 0x00000000 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb30214 │ 0x00000000 │
╰───────────────────────────────┴────────────┴────────────╯

```
Show all registers that have "_RD" in their name
```
noc register --search *_RD* --max all       
```
Output:
```
==== Device 0 - Location: 1-2
                      NOC0 Registers                       
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0xffb20208 │ 0x00000001 │
│ NIU_MST_RD_DATA_WORD_RECEIVED │ 0xffb2020c │ 0x00000009 │
│ NIU_MST_RD_REQ_SENT           │ 0xffb20214 │ 0x00000001 │
│ NIU_MST_RD_REQ_STARTED        │ 0xffb20238 │ 0x00000001 │
│ NIU_SLV_RD_RESP_SENT          │ 0xffb202c8 │ 0x00fb47c9 │
│ NIU_SLV_RD_DATA_WORD_SENT     │ 0xffb202cc │ 0x00fb47c5 │
│ NIU_SLV_RD_REQ_RECEIVED       │ 0xffb202d4 │ 0x00fb47c8 │
│ NOC_SEC_FENCE_FIFO_RDDATA     │ 0xffb204a8 │ 0x00000000 │
╰───────────────────────────────┴────────────┴────────────╯

                      NOC1 Registers                       
╭───────────────────────────────┬────────────┬────────────╮
│ Name                          │ Address    │ Value      │
├───────────────────────────────┼────────────┼────────────┤
│ NIU_MST_RD_RESP_RECEIVED      │ 0xffb30208 │ 0x00000000 │
...
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## r

### Usage

```
read <address> [ <word-count> ] [ --format=hex8 ] [ --unsafe ] [ -r <risc_name> ] [ -d <device> ] [ -l <loc> ]
```


### Description

Reads and prints a block of data from address 'address'.


### Arguments

- `address`: Address to read from
- `word-count`: Number of words to read. [Default: 1]


### Options

- `--format` = **\<F\>**: Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex8]
- `-r` = **\<risc_name\>**: RISC core name if you want to read memory that is not exposed on NOC.
- `--unsafe`: Experts mode, allow reading everything (bypass safety checks).


### Examples

Read 1 word from address 0
```
read 0x0 1                          
```
Output:
```
Device 0 [0x58506e131fe32c7b] | Location 1-2 (0,0) | Block l1 : 0x00000000 (1 bytes)
0x00000000:  93
```
Read 16 words from address 0
```
read 0x0 16                         
```
Output:
```
Device 0 [0x58506e131fe32c7b] | Location 1-2 (0,0) | Block l1 : 0x00000000 (16 bytes)
0x00000000:  93  02  00  00  13  03  00  00  63  80  62  0a  b7  12  b1  ff
```
Prints 32 bytes in i8 format
```
read 0x0 32 --format i8             
```
Output:
```
Device 0 [0x58506e131fe32c7b] | Location 1-2 (0,0) | Block l1 : 0x00000000 (32 bytes)
0x00000000:  147  2  0  0  19  3   0   0  99  128  98  10  183  18  177  255
0x00000010:  19   3  0  0  19  83  67  0  35  160  98  0   183  18  177  255
```
Read 16 words from brisc private data memory
```
read 0xFFB0000 -r brisc 16          
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
Print status
```
riscv status                    
```
Output:
```
  HALTED PC=0x00000160 - brisc 0,0 [0]
  IN RESET - trisc0 0,0 [0]
  IN RESET - trisc1 0,0 [0]
  IN RESET - trisc2 0,0 [0]
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
Output:
```
Setting breakpoint at address 0 for brisc 0,0 [0]
Setting breakpoint at address 0 for trisc0 0,0 [0]
Setting breakpoint at address 0 for trisc1 0,0 [0]
Setting breakpoint at address 0 for trisc2 0,0 [0]
```
Delete breakpoint
```
riscv bkpt del 0                
```
Output:
```
Deleting breakpoint 0 for brisc 0,0 [0]
Deleting breakpoint 0 for trisc0 0,0 [0]
Deleting breakpoint 0 for trisc1 0,0 [0]
Deleting breakpoint 0 for trisc2 0,0 [0]
```
Set a read watchpoint
```
riscv wchpt setr 0 0xc          
```
Output:
```
Setting read watchpoint at address 0 for brisc 0,0 [0]
Setting read watchpoint at address 0 for trisc0 0,0 [0]
Setting read watchpoint at address 0 for trisc1 0,0 [0]
Setting read watchpoint at address 0 for trisc2 0,0 [0]
```
Set a write watchpoint
```
riscv wchpt setw 0 0xc          
```
Output:
```
Setting write watchpoint at address 0 for brisc 0,0 [0]
Setting write watchpoint at address 0 for trisc0 0,0 [0]
Setting write watchpoint at address 0 for trisc1 0,0 [0]
Setting write watchpoint at address 0 for trisc2 0,0 [0]
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.
- `--risc, -r` = **\<risc-name\>**: RiscV name (e.g. brisc, triscs0, trisc1, trisc2, ncrisc, erisc). [default: all]






## run-elf / re

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






## server

### Usage

```
server start [--port <port>]
server stop
```


### Description

Starts or stops tt-exalens server.


### Examples

Command:
```
server start --port 5555
```
Output:
```
ttexalens-server listening on port 5555
```
Command:
```
server stop
```






## tensix-reg / reg

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
- `-n` = **\<noc-id\>**: NOC ID. Optional. Default: 0.


### Examples

Prints configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25)                            
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_a...
14
```
Prints debug register with address 0x54
```
reg dbg(0x54)                                       
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
570884107
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
PACK_CONFIG01_disable_pack_zero_flag
PACK_CONFIG01_reserved_0
PACK_CONFIG01_out_data_format
PACK_CONFIG01_in_data_format
PACK_CONFIG01_dis_shared_exp_assembler
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
```
Prints register with name UNPACK_CONFIG0_out_data_format
```
reg UNPACK_CONFIG0_out_data_format                  
```
Output:
```
Value of register UNPACK_CONFIG0_out_data_format on device 0 and location 0,0:
TensixDataFormat.Float32
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT  
```
Output:
```
Value of register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_a...
TensixDataFormat.Int8
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE                      
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
570884107
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18                            
```
Output:
```
Register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_address=None...
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0                
```
Output:
```
Register ConfigurationRegisterDescription(base_address=DeviceAddress(private_address=4293853184, noc_address=None, bar0_address=No...
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0                           
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0                                
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0                                  
```
Output:
```
Value of register DebugRegisterDescription(base_address=DeviceAddress(private_address=4289798144, noc_address=4289798144, bar0_add...
18
```


### Common options

- `--device, -d` = **\<device-id\>**: Device ID. Defaults to the current device.
- `--loc, -l` = **\<loc\>**: Grid location. Defaults to the current location.






## write-xy / wxy

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






