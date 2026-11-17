# How tt-exalens is built

This page explains the design, so that a change can follow it: how tt-exalens models a device, how it reaches the hardware, and what each kind of access costs and does to the device. Conventions for code and reviews are in [AGENTS.md](../AGENTS.md).

## Device model

- A `Context` holds the `Device`s, and a `Device` is one chip. A chip attached over PCIe is local. A chip reached over Ethernet through a local chip is remote.
- A device is a grid of blocks. `Device.block_types` (`ttexalens/device.py`) names every block type: `functional_workers` (Tensix), `eth`, `dram`, `arc`, `pcie`, `router_only`, Blackhole's `security` and `l2cpu`, and the harvested types `harvested_workers`, `harvested_eth` and `harvested_dram`, which are disabled on that chip. `Device.get_block_locations(block_type)` lists a type's blocks, and an `OnChipCoordinate` addresses one block.
- Each block is a `NocBlock` subclass under `ttexalens/hardware/<arch>/`.
- A block may have RISC cores (`NocBlock.all_riscs`, `debuggable_riscs`). On Quasar a block has NEOs, and each NEO has its own RISCs and its own debug bus (`get_debug_bus(neo_id)`).
- Registers are described in `RegisterStore`s (`ttexalens/register_store.py`), and debug-bus signals in `DebugBusSignalStore`s (`ttexalens/debug_bus_signal_store.py`). A named register or signal can be a field of a 32-bit word: its description carries a mask and a shift, and reading the name returns only that field. The description also says which word: a configuration register's index, or a debug signal's read selectors. To read whole words, read a description with a full mask (`RegisterStore.parse_register_description`), or read all four words of a debug-bus group with `DebugBusSignalStore.read_signal_group_unsafe(group)`. A register description's `size` is a multiple of 4 bytes and can span consecutive words; reading it reads them all.
- On some blocks, each NOC has its own copy of the NIU registers at one shared address. `RegisterDescription.noc_id` tells them apart, so a read through the other NOC sees the other copy.

## Memory maps

- Each block has a NOC memory map (`NocBlock.noc_memory_map`): the regions other agents reach over the NOC. Each RISC also has a memory map of the regions it addresses privately (`RiscInfo.memory_map`). A resource shared within the block appears in each map that can reach it, not always at the same address: Blackhole's `dest` is at the same address in every trisc's map, but Tensix thread 1's GPRs are `t1_gprs` at 0xFFE00100 in brisc's map and at 0xFFE00000 in trisc1's.
- Within one block, two map entries that hold the same `MemoryBlock` object are the same region. That is how a region of the NOC map shows up again in the RISC maps (for example `l1` and `debug_regs`), and how the trisc maps share Blackhole's `dest`. Compare map entries with each other, not with the block's own attributes: blocks of one type can share one cached map (`MemoryMap.get_memory_map_from_cache`), which holds the first block's objects. A name doesn't identify a region across maps: each RISC's own private memory is `data_private_memory` in its own map. And different objects can still be the same registers or memory: brisc's map and each trisc's map have their own entries for the Tensix GPRs and for `config_regs`, and on Blackhole each map has its own entry for another RISC's `<risc>.data_private_memory`.
- A map entry gives a region's address; it doesn't say which path reads it best. brisc's and the triscs' maps list the configuration registers as `config_regs` at their private address, and the select-register path in the next section reads them without a halt. The Ethernet maps have no `config_regs` region: on a Blackhole Ethernet block the registers read as zero through the select register at all 1,024 indices tried (one block, 2026-11).
- A region is a `MemoryMapBlockInfo` (`ttexalens/memory_map.py`): name, `MemoryBlock` (size and NOC, private and BAR0 addresses), `safe_to_read` (default: safe), `safe_to_write` (default: not safe) and `access_check` (for example, not while the RISC is in reset). The `find_by_*` methods look a region up by address or name.
- A region whose read is known to do harm must say `safe_to_read=False` in the architecture's map: a read that can hang the NOC or change what the device does (pop a queue, block, change a core's halt or reset state), or a read that returns wrong data. When only some reads of a region are bad, `safe_to_read` is a function of the address and size. Reads that only move counters, like the NIU counters below, stay safe. Callers should not keep their own lists.
- Marking a region in a NOC map stops every safe-mode caller from reading it. Marking one in a RISC map stops only callers that check the map, because private accesses aren't validated. Mark only what is known: seen on hardware, or stated in the ISA documentation. A new unsafe region goes into the map, marked, rather than being left out, so the map still says it exists.
- Safe mode, on by default, checks each NOC access against the target block's NOC map (`Device._validate_noc_access_is_safe`). It doesn't check BAR0 accesses or private-address accesses: `RiscDebug._validate_safe_access`, the hook for validating private accesses, is still empty.

## How reads reach the hardware

Every access takes one of three paths. Each path has its own cost and its own effect on the device.

| Path | Used for | Effect on the device | Speed (measured 2026-11) |
|---|---|---|---|
| NOC read | L1, DRAM, and memory-mapped registers | Doesn't halt or write. Register space goes through UMD's register API, 4 bytes at a time (`register_access`); bulk reads are for L1 and DRAM only | Wormhole n300: L1 4.2 GB/s on the local chip and 25 MB/s on the remote chip; registers 4.8 MB/s local and 0.18 MB/s remote |
| Debug hardware behind a select register | Debug-bus signals, Tensix configuration registers | Writes the select register, then reads the data register. Doesn't halt. A debug-bus group read given an L1 address uses that L1 as scratch space | About 140 KB/s: a Blackhole tile's 16,384 configuration registers in 0.47 s |
| RISC debug interface | GPRs and private memory of one RISC | Needs the core halted. `ensure_halted` halts a running core and continues it afterwards. A register with only a private address is read inside `ensure_private_memory_access`, which halts a running core. For a core in reset, it writes a jump-to-self at the core's start address in L1, takes the core out of reset, halts it, and afterwards puts it back in reset and restores the word | About 35 KB/s on Wormhole and 36 KB/s on Blackhole |

What follows from this:
- An API should make clear which path it takes. `RiscDebug.get_pc()` reads the PC over the debug bus when the core has a PC signal, and otherwise halts the core to read it.
- Reading a register can change other registers. The NIU counters count the reads that pass through them. The debug-bus and configuration reads write their select registers in `debug_regs`, and every read through a RISC's debug hardware writes its control register there. `debug_regs` also holds the wall clock (`RISCV_DEBUG_REG_WALL_CLOCK_*`, at +0x1F0 to +0x1F8), which changes between any two reads: its low word differed on 120 of 120 Blackhole Tensix tiles (2026-11). So two reads of register space can differ even when nothing else is running.
- A debug-bus read samples live signals, one 32-bit word per select write: `read_signal_group_unsafe` reads a group's four words one after another. A signal can change between reads whenever the hardware it watches is active, such as a running core or NOC traffic, including the reader's own.
- Code that stores a block's state reads in this order: the debug-bus groups, the register regions, L1, then the configuration registers. Its own reads change what later reads return, and this order keeps most of that out of what it stores. The stored `debug_regs` still holds the debug-bus select value the reader wrote last. Measured in 2026-11:
  - Wormhole: with the debug bus read after memory and the configuration registers, 221 of 785 sampled byte ranges of debug-bus data differed from live reads taken before and after the dump. With the debug bus read first, 105 did; that run also compared against four live reads instead of two.
  - Blackhole, on a hang: a NOC read of all of L1 sets `RISCV_DEBUG_REG_ECC_STATUS`. It read 0x0 on 120 of 120 Tensix tiles before the L1 read, and 0x80 on 64 of them after it.
- Reads of private memory and of RISC registers cost far more than NOC reads, so read them only when a NOC read can't get the same data.
- When no NOC is named, a read fails over to the other NOC if one hangs. A read that names its NOC doesn't fail over. `read_from_device` and the other `tt_exalens_lib` functions that resolve their NOC with `check_noc_id` pass the context's NOC when the caller gives none, so they don't fail over.

## RISC debug

- `RiscDebug` (`ttexalens/hardware/risc_debug.py`, `baby_risc_debug.py`) halts, continues and steps a RISC, and reads its status, GPRs (index 32 is the PC) and memory. Reading the debug hardware's status and watchpoint registers (`read_status`, `read_watchpoints_state`, `read_watchpoint_address`) sends the core no command and needs no halt. Reading a GPR (index 0 to 31) or memory makes the core run a debug-mode command, so the core must be halted: `read_memory` checks that, and `read_gpr` doesn't. On Wormhole and Blackhole, index 32 comes from the debug bus instead. `ensure_halted` is a context manager: it halts a running core and continues it on exit, and leaves an already-halted core halted.
- Not every RISC can be debugged. `BabyRiscInfo.debug_hardware_present` says which. On Wormhole and Blackhole, ncrisc has no debug hardware. A core in reset can't be halted.
- Some private regions are hardware queues or windows, not memory. Per the [ISA documentation](https://github.com/tenstorrent/tt-isa-documentation), reading a mailbox, PC buffer or TTSync register can pop a value or block. A debug read of such a region can also change what the core reports about its halt state: this was seen on Blackhole for the instruction buffers, PC buffers and mailboxes, on Wormhole for erisc code private memory, and on both for a trisc's `semaphores` region, where every trisc tried stopped reporting halted (2026-11). The Wormhole erisc map doesn't list its code private memory. The Tensix RISC maps list the other regions without marking them unsafe to read, and private accesses aren't validated, so nothing stops a debug read of them yet. No read of the trisc maps' `mop_config` has been tested: the maps put it at 0xFFB14000, where a Blackhole trisc's map also has brisc's data private memory, while tt-metal's `tensix.h` has `TENSIX_MOP_CFG_BASE` at 0xFFB80000.
- On Blackhole, a halted core can later report that it isn't halted, though nothing continued it, and `halt()` on it can then raise `RiscHaltError`. Seen in every triage run on one Blackhole board, and after debug memory reads (2026-11): the loss comes on the first region read after the halt, whichever region that is. In one run 96 of 384 cores lost the halt there and none did in 903 later reads; in a second run, with the regions in reverse order, 93 did, after 1 to 3 words. The word read just before the loss comes back wrong (0x0 or 0x1 seen), the rest of the read raises `<risc> is not halted`, and `halt()` on the core doesn't take again. GPR reads didn't trigger it. Whether the hardware or tt-exalens's debug-status reads cause it is unverified. Code that needs a halted core checks `is_halted()` after halting and after its reads.
- Known hardware limits:
  - Blackhole trisc2 private-memory reads are wrong at addresses with `addr % 16 > 4` (tt-exalens#528): 3 of 112 words differed at each of the offsets 8 and 12, and none at 0 or 4 (7 tiles, 2026-11). `BlackholeBabyRiscDebug.assert_trisc2_address` rejects any trisc2 read that starts at such an address. trisc2's reads of L1, `dest` and the configuration registers were right at every offset (the first 0x100 bytes of L1 and 0x400 bytes of the other two, 52 tiles), and so were its reads of the Tensix GPRs (1,216 words, 19 tiles).
  - Blackhole: a NOC read of a RISC's data private memory can break the device (tt-exalens#907). A RISC's debug read of another RISC's data private memory at those NOC addresses hung the tile on a dispatch core (2026-11). The maps list these regions with a check that refuses them while that RISC is in reset, and don't mark them unsafe to read yet.
  - On Wormhole and Blackhole, continuing a core after a halt and a read or write can break it (tt-exalens#908).

## Multi-chip

- A remote chip is reached through an Ethernet link of a local chip. Called on the remote device, `get_remote_transfer_eth_core()` returns the local chip's Ethernet core, in logical coordinates, that currently carries that traffic. On a local device it returns None. `UmdDevice` fails over only between the local chip's link cores, so the remote chip stays reachable while one of those works.
- A remote chip's own link cores are its only path to the host. On an n300, halting one cut the chip off until `tt-smi -r`, and so did reading the GPRs of a running one, once (2026-11). So send those cores no debug-mode command; their GPRs and private memory can't be read. Reading their status and watchpoint registers left the chip reachable (2 cores, 5 rounds of the three reads, idle n300), and so did halting the remote chip's Ethernet cores that have no link. `Device.active_eth_block_locations` lists a device's connected Ethernet blocks, which on a remote device include the link cores.
- Halting a local chip's link cores cuts off the chips reached through them (n300, 2026-11). Code that halts cores finishes each remote chip, halts included, before it starts on the chip that remote chip is reached through.

## Device backends

- A `Context` reaches devices through a `UmdApi` and its devices (`ttexalens/umd_api.py`, `ttexalens/umd_device.py`). `load_context` (`ttexalens/tt_exalens_init.py`) takes the `UmdApi`. The remote server's wrappers (`RemoteUmdApiWrapper` and `RemoteUmdDevice`, `ttexalens/server.py`) provide the same methods, so a new backend would be another implementation of that interface.

## Decoding

- ELF and DWARF parsing (`ttexalens/elf/`) reads typed variables through a `MemoryAccess`. Decoding works the same against a live device, a remote one, or plain bytes: `FixedMemoryAccess` (`ttexalens/memory_access.py`) wraps a byte buffer, so `ElfFile(path).read_global("mailboxes", FixedMemoryAccess(l1_bytes))` decodes L1 bytes with no device.

## Library API and CLI

- `ttexalens/tt_exalens_lib.py` is the public library. Its functions return data, for example `read_from_device` (bytes) and `get_tensix_state` (a `TensixState`); `coverage` is the one that writes files. Callers decide how to store or show the data.
- The CLI commands in `ttexalens/cli_commands/` sit on top of the library. Both feed the generated docs (AGENTS.md "Generated documentation").

## Where changes go

| Change | Where |
|---|---|
| A memory region or its safety | The architecture's block class, in the method that builds its memory maps (for example `_update_memory_maps` in `hardware/blackhole/functional_worker_block.py`) |
| A register description | `hardware/<arch>/*_registers.py` and the block's `RegisterStore` |
| A debug-bus signal | `hardware/<arch>/*_debug_bus_signals.py` |
| A library function | `ttexalens/tt_exalens_lib.py`, per AGENTS.md "Library API" |
| A CLI command | `ttexalens/cli_commands/`, per AGENTS.md "CLI commands" |
