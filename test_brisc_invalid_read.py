# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.elf_loader import ElfLoader
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.risc_debug import RiscHaltError
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens import tt_exalens_lib as lib

from ttexalens.rich_formatters import formatter

"""
This test compares the behavior of a BRISC RISC core when executing
program sequences that include both valid and various invalid/out-of-range
operations (e.g., memory reads or program counter jumps). The test runs
the core through defined valid and invalid scenarios for each fault type.
It captures and compares the internal signal states of the core during
both operations, highlighting any differences in behavior between a
successful execution and a triggered fault.

Sample Invalid Scenarios for Read Address Out of Range:
1. Invalid Memory Read (Type 1):
  lui a5,0x500      # a5 = 0x500 << 12 = 0x500000 (Out-of-range address, uses 0x500)
  lw a6,0(a5)       # a6 = MEM[a6 + 0]
  jump 0            # jump to offset address 0

2. Invalid Memory Read (Type 2):
  lui a5,0x400      # a5 = 0x400 << 12 = 0x400000 (Different Out-of-range address, uses 0x400)
  lw a6,0(a5)       # a6 = MEM[a6 + 0]
  jump 0            # jump to offset address 0

Sample Invalid Scenarios for Write Address Out of Range:
3. Invalid Memory Write (Type 1):
  lui a5,0x500      # a5 = 0x500 << 12 = 0x500000 (Out-of-range address, uses 0x500)
  sw a6,0(a5)       # MEM[a5 + 0] = a6
  jump 0

4. Invalid Memory Write (Type 2):
  lui a5,0x400      # a5 = 0x400 << 12 = 0x400000 (Different Out-of-range address, uses 0x400)
  sw a6,0(a5)       # MEM[a5 + 0] = a6
  jump 0
"""


# Global references
risc_name = "brisc"
context = init_ttexalens()
device = context.devices[0]
loc = OnChipCoordinate.create("0,0", device)
noc_block = device.get_block(loc)
risc_debug: BabyRiscDebug = noc_block.get_risc_debug(risc_name)
signal_store = noc_block.debug_bus
program_base_address = risc_debug.risc_info.get_code_start_address(risc_debug.register_store)

print(f"Program base address: 0x{program_base_address:x}")


def write_program(addr: int, data: int | list[int]):
    """Write program code data at specified address offset."""
    write_data_checked(program_base_address + addr, data)


def write_data_checked(addr: int, data: int | list[int]):
    """Write data to memory and verify it was written correctly."""
    if isinstance(data, int):
        lib.write_words_to_device(loc, addr, data, context=context)
        read_data = lib.read_word_from_device(loc, addr, context=context)
        assert read_data == data, f"Data verification failed at address {addr:x}"
    else:
        byte_data = b"".join(x.to_bytes(4, "little") for x in data)
        lib.write_to_device(loc, addr, byte_data, context=context)
        read_data = lib.read_from_device(loc, addr, num_bytes=len(byte_data), context=context)
        assert read_data == byte_data, f"Data verification failed at address {addr:x}"


# Cause an invalid read from l1 memory from out of range address
# lui_instr: The specific LUI instruction word (contains the immediate address part)
def cause_read_address_out_of_range(lui_instr: int, valid: bool):
    write_program(0, 0x00000013)  # nop
    write_program(4, lui_instr)  # lui a5,imm   (lui_instr is already prepared)
    if valid:
        # Repeating LW instruction for the valid case
        for i in range(8, 1000, 4):
            write_program(i, 0x0007A803)  # lw a6,0(a5) (lw to valid address)
        write_program(1000, ElfLoader.get_jump_to_offset_instruction(-992))
    else:
        # Execute only one LW instruction for the invalid case
        write_program(8, 0x0007A803)  # lw a6,0(a5) (lw to invalid address)
        write_program(12, ElfLoader.get_jump_to_offset_instruction(0))


# --- WRITE OUT OF RANGE ---
def cause_write_address_out_of_range(lui_instr: int, valid: bool):
    write_program(0, 0x00000013)  # nop
    write_program(4, lui_instr)  # lui a5,imm   (lui_instr is already prepared)
    write_program(8, 0x0000A5B7)  # lui a1, 10  (a1 = data to write)

    # SW instruction: sw a1, 0(a5) (0x00b7a023: sw a1, 0(a5))
    store_instr = 0x00B7A023

    if valid:
        # Repeating SW instruction for the valid case
        for i in range(12, 1000, 4):
            write_program(i, store_instr)
        write_program(1000, ElfLoader.get_jump_to_offset_instruction(-988))
    else:
        write_program(12, store_instr)  # sw a1, 0(a5) (sw to invalid address)
        write_program(14, 0x00000013)  # nop
        write_program(16, 0x00000013)  # nop
        write_program(20, store_instr)  # sw a1, 0(a5) (sw to invalid address)
        write_program(24, 0x00000013)  # nop
        write_program(28, 0x00000013)  # nop
        # write_program(32, store_instr) # sw a1, 0(a5) (sw to invalid address)
        # write_program(36, 0x00000013)  # nop
        # write_program(40, 0x00000013)  # nop
        # write_program(44, store_instr) # sw a1, 0(a5) (sw to invalid address)
        # write_program(48, 0x00000013)  # nop
        # write_program(52, 0x00000013)  # nop
        write_program(32, ElfLoader.get_jump_to_offset_instruction(0))


# -------------------------------------------


def cause_pc_jump_out_of_range(params: dict[str, int], valid: bool):
    # This function is retained for completeness in PROGRAM_CAUSES, but not used in the run loop below
    write_program(0, 0x00000013)  # nop
    if valid:
        write_program(4, 0x00000013)  # nop
        write_program(8, ElfLoader.get_jump_to_offset_instruction(0))
    else:
        instr = ElfLoader.get_jump_to_offset_instruction(2**7)
        i = 4
        while i < risc_debug.risc_info.l1.size - program_base_address:
            write_program(i, instr)
            i += 4


def halt_read_address_out_of_range(risc_debug: BabyRiscDebug, valid: bool):
    if valid:
        risc_debug.halt()
    else:
        try:
            risc_debug.halt()
            assert False, f"Expected halt to fail for invalid read, but it succeeded"
        except RiscHaltError as e:
            pass


def halt_write_address_out_of_range(risc_debug: BabyRiscDebug, valid: bool):
    risc_debug.halt()
    # moze li posle nesto


def halt_pc_jump_out_of_range(risc_debug: BabyRiscDebug, valid: bool):
    if valid:
        risc_debug.halt()
        # pass


TEST_SCENARIOS = {
    "read_address_out_of_range": {
        "lui_instr_valid": 0x00500793,  # lui a5,0x5 (Valid L1 address)
        # "lui_instr_invalid_1": 0x005007b7, # lui a5,0x500 (Invalid L1 address - Type 1)
        "lui_instr_invalid_1": 0x00A007B7,  # lui a5,0xa00 (Invalid L1 address - Type 1)
        "lui_instr_invalid_2": 0x00B007B7,  # lui a5,0xb00 (Invalid L1 address - Type 2, different address)
        "halt_handler": "read_address_out_of_range",
    },
    "write_address_out_of_range": {
        "lui_instr_valid": 0x00500793,  # lui a5,0x5 (Valid L1 address)
        "lui_instr_invalid_1": 0x005007B7,  # lui a5,0x500 (Invalid L1 address - Type 1)
        "lui_instr_invalid_2": 0x006007B7,  # lui a5,0x600 (Invalid L1 address - Type 2, different address)
        "halt_handler": "write_address_out_of_range",
    },
    "pc_jump_out_of_range": {
        "lui_instr_valid": 0,
        "lui_instr_invalid_1": 0,
        "lui_instr_invalid_2": 0,
        "halt_handler": "pc_jump_out_of_range",
    },
}
# -------------------------------

# --- UPDATING PROGRAM_CAUSES AND HALT_HANDLERS ---
PROGRAM_CAUSES = {
    "read_address_out_of_range": cause_read_address_out_of_range,
    "write_address_out_of_range": cause_write_address_out_of_range,  # Added new cause function
    "pc_jump_out_of_range": cause_pc_jump_out_of_range,
}

HALT_HANDLERS = {
    "read_address_out_of_range": halt_read_address_out_of_range,
    "write_address_out_of_range": halt_write_address_out_of_range,  # Added new halt handler
    "pc_jump_out_of_range": halt_pc_jump_out_of_range,
}
# ---------------------------------------------------

# run_and_sample now takes the LUI instruction and the cause name
def run_and_sample(lui_instr: int, cause_name: str, valid: bool):
    # Load program
    # write_program(0, 0x00100073)  # ebreak

    # Call the program setup function with the desired LUI instruction
    PROGRAM_CAUSES[cause_name](lui_instr, valid)

    # take core out of reset
    risc_debug.set_reset_signal(False)
    assert not risc_debug.is_in_reset()

    import time

    time.sleep(0.4)  # wait a bit for core to start executing

    # Use the appropriate Halt Handler for the test (e.g., "read_address_out_of_range" or "write_address_out_of_range")
    HALT_HANDLERS[cause_name](risc_debug, valid)

    # Sample signals
    samples: dict[str, list[int]] = {}
    # for group in signal_store.group_names:
    #     group_values = signal_store._read_signal_group_samples(group, l1_addr)
    #     samples[group] = group_values
    return samples


# Stop risc with reset
risc_debug.set_reset_signal(True)
assert risc_debug.is_in_reset()

l1_addr = 0x1000

# --- UPDATING TESTS_TO_RUN ---
# TESTS_TO_RUN = ["read_address_out_of_range", "write_address_out_of_range", "pc_jump_out_of_range"]
TESTS_TO_RUN = ["pc_jump_out_of_range"]
# -----------------------------

for test_name in TESTS_TO_RUN:
    test_params = TEST_SCENARIOS[test_name]
    # The cause_name is now dynamically retrieved from the test_name
    cause_name = test_name

    formatter.print_section_header(f"--- STARTING TEST: {test_name.upper()} ---", style="bold green")

    # 1. VALID example
    risc_debug.set_reset_signal(True)
    assert risc_debug.is_in_reset()

    lui_instr_valid = test_params["lui_instr_valid"]
    print(f"Starting valid case (lui: 0x{lui_instr_valid:x})...")
    valid_samples = run_and_sample(lui_instr_valid, cause_name, valid=True)

    # 2. INVALID example 1
    risc_debug.set_reset_signal(True)
    assert risc_debug.is_in_reset()

    lui_instr_invalid_1 = test_params["lui_instr_invalid_1"]
    print(f"Starting invalid case 1 (lui: 0x{lui_instr_invalid_1:x})...")
    invalid_samples_1 = run_and_sample(lui_instr_invalid_1, cause_name, valid=False)

    try:
        risc_debug.halt()
        risc_debug.write_memory(0xFFB00000, 0x12345678)
        ret = risc_debug.read_memory(0xFFB00000)
        assert ret != 0x12345678
    except RiscHaltError as e:
        pass

    # # RECOVERY?
    # risc_debug.set_reset_signal(True)
    # assert risc_debug.is_in_reset()

    # write_program(0, ElfLoader.get_jump_to_offset_instruction(0))

    # risc_debug.set_reset_signal(False)
    # assert not risc_debug.is_in_reset()

    # risc_debug.halt()
    # assert risc_debug.is_halted()

    # risc_debug.write_memory(0xFFB00000, 0x12345678)
    # ret = risc_debug.read_memory(0xFFB00000)
    # assert ret == 0x12345678

    # 3. INVALID example 2

    # risc_debug.set_reset_signal(True)
    # assert risc_debug.is_in_reset()

    # lui_instr_invalid_2 = test_params["lui_instr_invalid_2"]
    # print(f"Starting invalid case 2 (lui: 0x{lui_instr_invalid_2:x})...")
    # invalid_samples_2 = run_and_sample(lui_instr_invalid_2, cause_name, valid=False)

    # # Display comparison
    # def format_for_display(val):
    #     if isinstance(val, int):
    #         return f"0x{val:x}"
    #     return str(val)

    # # Defining columns for 3 samples
    # COLUMNS = [
    #     ("Signal Name", ""),
    #     ("Valid", "green"),
    #     (f"Invalid 1 (0x{lui_instr_invalid_1:x})", "green"),
    #     # (f"Invalid 2 (0x{lui_instr_invalid_2:x})", "green"),
    # ]

    # grouped_data_for_rich = {}
    # grouping_layout = []

    # # Iterate through signal groups
    # for group in sorted(signal_store.group_names):

    #     try:
    #         valid_group = valid_samples[group][0]
    #         invalid_group_1 = invalid_samples_1[group][0]
    #         # invalid_group_2 = invalid_samples_2[group][0]
    #     except (KeyError, IndexError):
    #         # Skip if any sample group is missing
    #         continue

    #     table_rows = []
    #     difference_found_in_group = False

    #     # Iterate through individual signals
    #     for signal_name in sorted(valid_group.keys()):
    #         v_val = valid_group[signal_name]
    #         i1_val = invalid_group_1[signal_name]
    #         # i2_val = invalid_group_2[signal_name]

    #         # Check if values differ in ANY of the 3 cases (V != I1 OR V != I2 OR I1 != I2)
    #         # is_different = not (v_val == i1_val and i1_val == i2_val)

    #         v_display = format_for_display(v_val)
    #         i1_display = format_for_display(i1_val)
    #         # i2_display = format_for_display(i2_val)

    #         signal_name_display = f"[bold green]{signal_name}[/bold green]"

    #         # Formatting cells based on difference
    #         v_cell = v_display
    #         i1_cell = i1_display
    #         # i2_cell = i2_display

    #         if is_different:
    #             difference_found_in_group = True

    #             # Check and color the Valid column
    #             if v_val != i1_val or v_val != i2_val:
    #                 v_cell = f"[bold green]{v_display}[/bold green]"

    #             # Check and color the Invalid 1 column
    #             if i1_val != v_val or i1_val != i2_val:
    #                 i1_cell = f"[bold green]{i1_display}[/bold green]"

    #             # Check and color the Invalid 2 column
    #             if i2_val != v_val or i2_val != i1_val:
    #                 i2_cell = f"[bold green]{i2_display}[/bold green]"

    #             # Color the signal name if a difference was found
    #             signal_name_display = f"[bold green]{signal_name}[/bold green]"

    #         row = (signal_name_display, v_cell, i1_cell, i2_cell)
    #         if is_different:
    #             table_rows.append(row)

    #     # Display only groups where a difference was found
    #     if difference_found_in_group:
    #         grouped_data_for_rich[group] = table_rows
    #         grouping_layout.append([group])

    # formatter.print_section_header(
    #     f"RISC Signal Comparison ({risc_name.upper()} @ {loc.to_str('noc0')}) - 3 Cases", style="bold green"
    # )
    # formatter.display_grouped_data(
    #     data=grouped_data_for_rich, columns=COLUMNS, grouping=grouping_layout, simple_print=False
    # )
    # print("\n" + "=" * 80 + "\n")


# ONLY TESTED ON WORMHOLE
"""
pc - out of range - it represents adcs when combined - nije uvek
adcs0_unpacker0_channel0_w_cr = 0x28
adcs0_unpacker0_channel0_w_counter = 0xd9
adcs0_unpacker0_channel0_z_cr = 0xc9
adcs0_unpacker0_channel0_z_counter = 0xab
Spoji ih: 0x28d9c9ab.

vrednost lebdi na magistrali

brisc_i_instrn - input instruction: same as pc - The processor wasn't receiving real instructions. Instead, because the bus was hung,
the data lines were just "echoing" the address lines (or the stuck unpacker values) - reading from dead memory - bus is floating
valid only when brisc_i_instrn_vld is set -> instruction that has just been fetched
pc of instruction and instruction itself are the same

could not sample signals because there are other requests pending on the memory

memory controller receives read request for out of range address, does not respond because of invalid address, bus hangs
pipelining causes processor to continue issuing read requests to the next predicted invalid addresses, bus remains hung
brisc_icache_req_fifo_full = True
"""


"""
invalid read from l1 memory from out of range address
- brisc_pc - we know exact instruction that caused the fault - lui a5,0x500; lw a6,0(a5).    - we cannot see what value is a5
- brisc_if_invalid_instrn = 1
- brisc_rv_out_dmem_rden = 1
- brisc_dbg_obs_cmt_vld = 0 -> true if the Load/Store Unit's retire-order queue contains at least one instruction, and the instruction that
will retire next meets the requirements for leaving the Load/Store Unit, false otherwise. Retire - faza when instruction is completed and
its results are written back to the register file or memory.
- ..._i_mailbox_rd_type za brisc and trisci have value 0x5 for valid and 0x4 for invalid write address - on bh are completely different, so it is not relevant
- brisc_target_intf = 0 - memory interface is not valid
- brisc_dbg_obs_mem_addr - address that caused the fault - we cannot see what value is a5.      ?
+ da li moze da se hanguje


invalid write to l1 memory from out of range address
- brisc_pc - we know exact instruction that caused the fault - sw a6,0(a5).    - we cannot see what value is a5
- brisc_if_invalid_instrn = 1
- brisc_rv_out_dmem_wren = 1
- brisc_dbg_obs_cmt_vld = 0 -> true if the Load/Store Unit
- ..._i_mailbox_rd_type za brisc and trisci have value 0x5 for valid and 0x4 for invalid write address - on bh are completely different, so it is not relevant
- brisc_target_intf = 0 - memory interface is not valid
"""
