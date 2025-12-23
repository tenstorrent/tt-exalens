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
- `-d` = **\<D\>**: Device ID. Optional and repeatable. Default: current device


### Examples

Read 1 word from address 0
```
brxy 0,0 0x0 1
```
Read 16 words from address 0
```
brxy 0,0 0x0 16
```
Prints 32 bytes in i8 format
```
brxy 0,0 0x0 32 --format i8
```
Sample for 5 seconds
```
brxy 0,0 0x0 32 --format i8 --sample 5
```
Read 16 words from dram channel 0
```
brxy ch0 0x0 16
```


### Common options







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


### Common options







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
List all predefined debug bus signals
```
debug-bus list-signals --max all
```
List up to 5 signals whose names contain 'pc'
```
debug-bus list-signals --search *pc* --max 5
```
List all debug bus signal groups
```
debug-bus list-groups
```
List groups whose names match pattern 'brisc'
```
debug-bus list-groups --search brisc*
```
List all signals in group 'brisc_group_a' using L1 sampling, 4 samples, 10 cycles interval
```
debug-bus group brisc_group_a 0x1000 --samples 4 --sampling-interval 10
```
List all signals in group 'brisc_group_a' that ends with 'pc' using L1 sampling
```
debug-bus group brisc_group_a 0x1000 --search *pc
```
Print values for trisc0_pc and trisc1_pc
```
debug-bus trisc0_pc,trisc1_pc
```
Print value for a custom signal and trisc2_pc
```
debug-bus {7,0,12,0x3ffffff},trisc2_pc
```


### Common options







## device / d

### Usage

```
device [-d <device-id>] [<axis-coordinate> [<cell-contents>]] [--no-legend]
```


### Description

Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.


### Arguments

- `device-id`: ID of the device [default: all]
- `axis-coordinate`: Coordinate system for the axis [default: logical-tensix] Supported: noc0, noc1, translated, die, logical-tensix, logical-eth, logical-dram
- `cell-contents`: A comma separated list of the cell contents [default: riscv] Supported: riscv - show the status of the RISC-V ('R': running, '-': in reset), or block type if there are no RISC-V cores block - show the type of the block at that coordinate logical, noc0, noc1, translated, die - show coordinate noc0_id - show the NOC0 node ID (x-y) for the block noc1_id - show the NOC1 node ID (x-y) for the block


### Examples

Shows the status of the RISC-V for all devices
```
device
```
Shows the status of the RISC-V on noc0 axis for all devices
```
device noc0
```
Shows noc0 coordinates on logical tensix axis for all devices
```
device logical-tensix noc0
```
Shows the block type in noc0 axis for all devices without legend
```
device noc0 block --no-legend
```
Shows the status of the RISC-V on die axis for device 0
```
device -d 0 die
```
Shows noc0 coordinates on logical dram axis for device 0
```
device -d 0 logical-dram noc0
```
Shows the block type on noc0 axis for device 0 without legend
```
device -d 0 noc0 block --no-legend
```


### Common options







## tensix

### Usage

```
dump-tensix-reg [ <reg-group> ] [ -d <device> ] [ -l <loc> ] [ -v ] [ -t <thread-id> ]
```


### Options

- `reg-group`: Tensix register group to dump. Options: [all, alu, pack, unpack, gpr] Default: all
- `-v`: Verbose mode. Prints all general purpose registers.
- `-t` = **\<thread-id\>**: Thread ID. Options: [0, 1, 2] Default: all Description: Prints the tensix register group of the given name, at the specified location and device.


### Examples

Prints all tensix registers for current device and core
```
tensix
```
Prints all tensix registers for device with id 0 and current core
```
tensix -d 0
```
Prints all tensix registers for current device and core at location 0,0
```
tensix -l 0,0
```
Prints all tensix registers for current device and core
```
tensix all
```
Prints alu configuration registers for current device and core
```
tensix alu
```
Prints packer's configuration registers for current device and core
```
tensix pack
```
Prints unpacker's configuration registers for current device and core
```
tensix unpack
```
Prints general purpose registers for current device and core
```
tensix gpr
```
Prints all general purpose registers for current device and core
```
tensix gpr -v
```
Prints general purpose registers for threads 0 and 1 for current device and core
```
tensix gpr -t 0,1
```


### Common options







## dump-coverage / cov

### Usage

```
dump-coverage <elf> <gcda_path> [<gcno_copy_path>] [-d <device>...] [-l <loc>]
```


### Description

Get coverage data for a given ELF. Extract the gcda from the given core
and place it into the output directory along with its gcno.


### Arguments

- `device`: ID of the device [default: current active]
- `loc`: Location identifier (e.g. 0-0) [default: current active]
- `elf`: Path to the currently running ELF
- `gcda_path`: Output path for the gcda
- `gcno_copy_path`: Optional path to copy the gcno file


### Examples

Pre-requisite: we have to run the elf before running coverage
```
re build_riscv/wormhole/cov_test.coverage.brisc.elf -r brisc
```
Command:
```
cov build_riscv/wormhole/cov_test.coverage.brisc.elf cov_test.gcda cov_test.gcno
```


### Common options







## dump-gpr / gpr

### Usage

```
gpr [ <reg-list> ] [ -v ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]
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
Command:
```
gpr ra,sp,pc
```


### Common options







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
Prints status registers with simple output
```
noc status -s
```
Prints a specific register value
```
noc register NIU_MST_RD_REQ_SENT
```
Prints multiple registers
```
noc register NIU_MST_RD_REQ_SENT,NIU_MST_RD_DATA_WORD_RECEIVED
```
Show all registers that have "_RD" in their name
```
noc register --search *_RD* --max all
```


### Common options







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
Prints debug register with address 0x54
```
reg dbg(0x54)
```
Prints names of first 10 registers that start with PACK
```
reg --search PACK*
```
Prints names of first 5 registers that start with ALU
```
reg --search ALU* --max 5
```
Prints names of all registers that include word format
```
reg --search *format* --max all
```
Prints register with name UNPACK_CONFIG0_out_data_format
```
reg UNPACK_CONFIG0_out_data_format
```
Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
```
reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT
```
Prints debug register with address 0x54 in integer format
```
reg dbg(0x54) --type INT_VALUE
```
Writes 18 to debug register with address 0x54
```
reg dbg(0x54) --write 18
```
Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
```
reg cfg(1,0x1E000000,25) --write 0x0
```
Prints debug register with address 0x54 for device 0 and core at location 0,0
```
reg dbg(0x54) -d 0 -l 0,0
```
Prints debug register with address 0x54 for core at location 0,0
```
reg dbg(0x54) -l 0,0
```
Prints debug register with address 0x54 for device 0
```
reg dbg(0x54) -d 0
```


### Common options







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
Command:
```
wxy 0,0 0x0 0x1234 --repeat 10
```
