# How tt-exalens is built

This page explains the design of tt-exalens: how it models a device, how it reaches the hardware, and what each kind of access costs and does to the device. Conventions for code and reviews are in [AGENTS.md](../AGENTS.md).

## Device model

A `Context` holds the `Device`s, and a `Device` is one chip. A chip attached over PCIe is local; a chip reached over Ethernet through a local chip is remote.

A device is a grid of blocks. `Device.block_types` (`ttexalens/device.py`) names every block type: `functional_workers` (Tensix), `eth`, `dram`, `arc`, `pcie`, `router_only`, Blackhole's `security` and `l2cpu`, and the harvested types `harvested_workers`, `harvested_eth` and `harvested_dram`, which are disabled on that chip. `Device.get_block_locations(block_type)` lists a type's blocks, and an `OnChipCoordinate` addresses one block.

Each block is a `NocBlock` subclass under `ttexalens/hardware/<arch>/`. A block may have RISC cores (`NocBlock.all_riscs`, `debuggable_riscs`). On Quasar a block has NEOs, and each NEO has its own RISCs and its own debug bus (`get_debug_bus(neo_id)`).

Registers are described in `RegisterStore`s (`ttexalens/register_store.py`), and debug-bus signals in `DebugBusSignalStore`s (`ttexalens/debug_bus_signal_store.py`). A named register or signal can be a field of a 32-bit word: its description carries a mask (a register's also a shift), and reading the name returns only that field. The description also says which word it is in: a configuration register's index, or a debug signal's read selectors. To read whole words, read a description with a full mask (`RegisterStore.parse_register_description`), or read all four words of a debug-bus group with `DebugBusSignalStore.read_signal_group_unsafe(group)`. A register description's `size` is a multiple of 4 bytes and can span consecutive words; reading it reads them all.

On some blocks each NOC has its own copy of the NIU registers at one shared address. `RegisterDescription.noc_id` tells them apart, so a read through the other NOC sees the other copy.

## Memory maps

A memory map lists the regions of a block and where they are. Each block has a NOC memory map (`NocBlock.noc_memory_map`), with the regions that can be reached over the NOC. Each RISC also has a memory map of the regions it addresses privately (`RiscInfo.memory_map`). A resource shared within the block appears in each map that can reach it, and not always at the same address: Blackhole's `dest` is at the same address in every trisc's map, but Tensix thread 1's GPRs are `t1_gprs` at 0xFFE00100 in brisc's map and at 0xFFE00000 in trisc1's.

A region is a `MemoryMapBlockInfo` (`ttexalens/memory_map.py`). It has a name, a `MemoryBlock` (the size, and the NOC, private and BAR0 addresses), and three things that say whether it may be accessed:

| Field | Meaning | Default |
|---|---|---|
| `safe_to_read` | whether a read is harmless; a value, or a function of the address and size | safe |
| `safe_to_write` | the same for a write | not safe |
| `access_check` | a condition that must hold at the time of the access, for example that the RISC is out of reset | none |

The `find_by_*` methods of a map look a region up by address or by name.

A region is marked `safe_to_read=False` when a read of it is known to do harm: it can break or hang the device, change what the device does (pop a queue, block, change what a core reports about its halt state), or return wrong data. Reads that only move counters, like the NIU counters below, are not marked.

Safe mode, which is on by default, checks each NOC access against the target block's NOC map (`Device._validate_noc_access_is_safe`). It doesn't check BAR0 accesses or private-address accesses: `RiscDebug._validate_safe_access`, the hook for validating private accesses, is still empty. So a mark in a NOC map is enforced, while a mark in a RISC map only informs code that asks the map.

A map entry gives a region's address; it doesn't say which path reads it best. For example, brisc's and the triscs' maps list the configuration registers as `config_regs` at their private address, while the select-register path in the next section reads them without halting anything.

## How reads reach the hardware

Every access takes one of three paths. Each path has its own cost and its own effect on the device.

| Path | Used for | Effect on the device | Speed (measured 2026-11) |
|---|---|---|---|
| NOC read | L1, DRAM, and memory-mapped registers | Doesn't halt or write. Register space goes through UMD's register API, 4 bytes at a time (`register_access`); bulk reads are for L1 and DRAM only | Wormhole n300: L1 4.2 GB/s on the local chip and 25 MB/s on the remote chip; registers 4.8 MB/s local and 0.18 MB/s remote |
| Debug hardware behind a select register | Debug-bus signals, Tensix configuration registers | Writes the select register, then reads the data register. Doesn't halt. A debug-bus group read given an L1 address uses that L1 as scratch space | About 140 KB/s: a Blackhole tile's 16,384 configuration registers in 0.47 s |
| RISC debug interface | GPRs and private memory of one RISC | Needs the core halted. `ensure_halted` halts a running core and continues it afterwards. A register with only a private address is read inside `ensure_private_memory_access`, which halts a running core. For a core in reset, it writes a jump-to-self at the core's start address in L1, takes the core out of reset, halts it, and afterwards puts it back in reset and restores the word | About 35 KB/s on Wormhole and 36 KB/s on Blackhole |

A few things follow from this.

**The path decides the side effects, so an API should make clear which one it takes.** `RiscDebug.get_pc()` reads the PC over the debug bus when the core has a PC signal, and otherwise halts the core to read it.

**Reading a register can change other registers.** The NIU counters count the reads that pass through them. The debug-bus and configuration reads write their select registers in `debug_regs`, and every read through a RISC's debug hardware writes its control register there. `debug_regs` also holds the wall clock (`RISCV_DEBUG_REG_WALL_CLOCK_*`), which differs between any two reads. So two reads of register space can differ even when nothing else is running.

**A debug-bus read samples live signals.** It reads one 32-bit word per select write, and `read_signal_group_unsafe` reads a group's four words one after another. A signal can change between those reads whenever the hardware it watches is active, such as a running core or NOC traffic, including the reader's own.

**Reads through a RISC cost far more than NOC reads.** Private memory and RISC registers are worth reading that way only when a NOC read can't get the same data.

**A read that names its NOC doesn't fail over.** When no NOC is named, a read fails over to the other NOC if one hangs. `read_from_device`, `write_to_device` and their word variants pass the context's NOC when the caller gives none (`check_noc_id`), so they don't fail over.

## RISC debug

`RiscDebug` (`ttexalens/hardware/risc_debug.py`, `baby_risc_debug.py`) halts, continues and steps a RISC, and reads its status, GPRs and memory. What a read needs depends on what it reads:

| Read | Needs the core halted | Notes |
|---|---|---|
| Status and watchpoint registers of the debug hardware (`read_status`, `read_watchpoints_state`, `read_watchpoint_address`) | no | sends the core no command |
| A GPR, index 0 to 31 | yes | the core runs a debug-mode command; `read_gpr` doesn't check that the core is halted |
| The PC, index 32 | no on Wormhole and Blackhole | it comes from the debug bus there |
| Memory | yes | the core runs a debug-mode command; `read_memory` checks that the core is halted |

`ensure_halted` is a context manager: it halts a running core and continues it on exit, and leaves an already-halted core halted.

Not every RISC can be debugged. `BabyRiscInfo.debug_hardware_present` says which. On Wormhole and Blackhole, ncrisc has no debug hardware. A core in reset can't be halted.

Some private regions are hardware queues or windows, not memory, and a read there is an operation. The mailboxes and PC buffers are FIFOs: per the [ISA documentation](https://github.com/tenstorrent/tt-isa-documentation), a read pops a value, and on an empty FIFO it doesn't return. A read of a TTSync register waits until the coprocessor has finished. A debug read of an instruction buffer or of the `semaphores` region made the core stop reporting halted (2026-11). The Wormhole and Blackhole Tensix RISC maps mark all of these `safe_to_read=False`. The Wormhole erisc map doesn't list the core's code private memory, where a debug read had the same effect.

Known hardware limits:

- **Blackhole, data private memory over the NOC.** A NOC read of a RISC's data private memory can break the device (tt-exalens#907), and a debug read of it through another RISC hung the tile. The NOC map and the other RISCs' maps mark these regions `safe_to_read=False`, so safe mode refuses the NOC read.
- **Blackhole, trisc2.** trisc2's debug reads of its own data private memory are wrong at addresses with `addr % 16 > 4` (tt-exalens#528). `BlackholeBabyRiscDebug.assert_trisc2_address` rejects any trisc2 read that starts at such an address.
- **Wormhole and Blackhole, continuing a core.** Continuing a core after a halt and a read or write can break it (tt-exalens#908).
- **Blackhole, a halt that doesn't hold.** A halted core can stop reporting halted on its first debug memory read, though nothing continued it. The cause isn't known. Code that needs the core halted should check `is_halted()` after halting and after reading.

## Multi-chip

A remote chip is reached through an Ethernet link of a local chip. Called on the remote device, `get_remote_transfer_eth_core()` returns the local chip's Ethernet core, in logical coordinates, that currently carries that traffic; on a local device it returns None. `UmdDevice` fails over only between the local chip's link cores, so the remote chip stays reachable while one of those works.

This makes debug access to Ethernet cores delicate:

- **A remote chip's own link cores are its only path to the host.** On an n300, halting one cut the chip off until `tt-smi -r`, and so did reading the GPRs of a running one, once (2026-11). Their GPRs and private memory can't be read without that risk. Reading their status and watchpoint registers left the chip reachable, and so did halting the remote chip's Ethernet cores that have no link.
- **Halting a local chip's link cores cuts off the chips reached through them** (n300, 2026-11). A tool that halts cores should finish each remote chip before it starts on the chip that remote chip is reached through.

`Device.active_eth_block_locations` lists a device's connected Ethernet blocks, which on a remote device include the link cores.

## Device backends

A `Context` reaches devices through a `UmdApi` and its devices (`ttexalens/umd_api.py`, `ttexalens/umd_device.py`). `load_context` (`ttexalens/tt_exalens_init.py`) takes the `UmdApi`. The remote server's wrappers (`RemoteUmdApiWrapper` and `RemoteUmdDevice`, `ttexalens/server.py`) provide the same methods, so a new backend would be another implementation of that interface.

## Decoding

ELF and DWARF parsing (`ttexalens/elf/`) reads typed variables through a `MemoryAccess`. Decoding works the same against a live device, a remote one, or plain bytes: `FixedMemoryAccess` (`ttexalens/memory_access.py`) wraps a byte buffer, so `ElfFile(path).read_global("mailboxes", FixedMemoryAccess(l1_bytes))` decodes L1 bytes with no device.

## Library API and CLI

`ttexalens/tt_exalens_lib.py` is the public library. Its functions return data, for example `read_from_device` (bytes) and `get_tensix_state` (a `TensixState`); `coverage` is the one that writes files. Callers decide how to store or show the data.

The CLI commands in `ttexalens/cli_commands/` sit on top of the library. Both feed the generated docs (AGENTS.md "Generated documentation").

## Where changes go

| Change | Where |
|---|---|
| A memory region or its safety | The architecture's block class, in the method that builds its memory maps (for example `_update_memory_maps` in `hardware/blackhole/functional_worker_block.py`) |
| A register description | `hardware/<arch>/*_registers.py` and the block's `RegisterStore` |
| A debug-bus signal | `hardware/<arch>/*_debug_bus_signals.py` |
| A library function | `ttexalens/tt_exalens_lib.py`, per AGENTS.md "Library API" |
| A CLI command | `ttexalens/cli_commands/`, per AGENTS.md "CLI commands" |
