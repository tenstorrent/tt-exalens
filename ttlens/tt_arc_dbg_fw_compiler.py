import os
from typing import Union, List
from ttlens.tt_arc_dbg_fw_log_context import LogInfo, ArcDfwLogContext, ArcDfwLogContextFromList, ArcDfwLogContextFromYaml
from math import floor
import struct

# TODO rework
def parse_elf_symbols() -> dict:
    file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", "fw/arc/arc_dbg_fw.syms")
    symbol_table = {}

    with open(file_name, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or "SYMBOL TABLE" in line or line.startswith("arc_dbg_fw"):
            continue
        
        parts = line.split()
        if len(parts) < 6:
            continue 

        address, flags, _type, section, size, name = parts[:6]
        
        if name==None or  name == "":
            continue

        symbol_table[name] = address

    return symbol_table

def change_byte_at_address(hex_lines: List[int], address: int, new_byte: int) -> List[int]:
    """
    Changes a single byte at the specified address in the hex lines.

    Args:
        hex_lines (List[int]): List of hex lines.
        address (int): Address to change the byte.
        new_byte (int): New byte value.

    Returns:
        List[int]: Updated list of hex lines.
    """
    line_index = address // 4
    byte_index = address % 4
    line = hex_lines[line_index]
    line = int.from_bytes(line.to_bytes(4, byteorder='big'), byteorder='little')
    mask = 0xFF << (byte_index * 8)
    new_line = (line & ~mask) | (new_byte << (byte_index * 8))
    new_line = int.from_bytes(new_line.to_bytes(4, byteorder='little'), byteorder='big')
    hex_lines[line_index] = new_line
    return hex_lines

def change_two_bytes_at_address(hex_lines: List[int], address: int, new_bytes: int) -> List[int]:
    """
    Changes two bytes at the specified address in the hex lines.

    Args:
        hex_lines (List[int]): List of hex lines.
        address (int): Address to change the bytes.
        new_bytes (int): New bytes value.

    Returns:
        List[int]: Updated list of hex lines.
    """
    line_index = address // 4
    byte_index = address % 4
    line = hex_lines[line_index]
    line = int.from_bytes(line.to_bytes(4, byteorder='big'), byteorder='little')
    mask = 0xFFFF << (byte_index * 8)
    new_line = (line & ~mask) | (new_bytes << (byte_index * 8))
    new_line = int.from_bytes(new_line.to_bytes(4, byteorder='little'), byteorder='big')
    hex_lines[line_index] = new_line
    return hex_lines

def change_four_bytes_at_address(hex_lines: List[int], address: int, new_bytes: int) -> List[int]:
    """
    Changes four bytes at the specified address in the hex lines.

    Args:
        hex_lines (List[int]): List of hex lines.
        address (int): Address to change the bytes.
        new_bytes (int): New bytes value.

    Returns:
        List[int]: Updated list of hex lines.
    """
    line_index = address // 4
    new_bytes = int.from_bytes(new_bytes.to_bytes(4, byteorder='big'), byteorder='little')
    hex_lines[line_index] = new_bytes
    return hex_lines

def load_hex_file(file_path: str) -> List[int]:
    """
    Loads a hex file into a list of hex lines.

    Args:
        file_path (str): Path to the hex file.

    Returns:
        List[int]: List of hex lines.
    """
    with open(file_path, 'r') as file:
        hex_lines = [int(line, 16) for line in file.read().splitlines()]
    return hex_lines

def save_hex_file(file_path: str, hex_lines: List[int]) -> None:
    """
    Saves the hex lines to a file.

    Args:
        file_path (str): Path to the hex file.
        hex_lines (List[int]): List of hex lines to save.
    """
    with open(file_path, 'w') as file:
        file.write('\n'.join(f'{line:08x}' for line in hex_lines))

def create_load_instruction(register: int, address: int) -> List[int]:
    """
    Creates an 8 byte load instruction for the specified register and address.

    Args:
        register (int): Register to load.
        address: Address to load from.

    Returns:
        List[int]: Load instruction.
    """
    instruction = 0x16007801 | (register & 0b111111)
    return [
        (instruction >> 24) & 0xFF,
        (instruction >> 16) & 0xFF,
        (instruction >> 8) & 0xFF,
        instruction & 0xFF,
        (address >> 24) & 0xFF,
        (address >> 16) & 0xFF,
        (address >> 8) & 0xFF,
        address & 0xFF
    ]

def create_store_instruction(r_addr: int,r_data :int, offset: int) -> List[int]:
    """
    Creates a 2 byte store instruction for the specified register and offset.

    Args:
        register (int): Register to store.
        offset (int): Offset to store to.

    Returns:
        List[int]: Store instruction.
    """
    # ST_S b,[SP,u7] 11000bbb010uuuuu
    opcode = 0b10100 << 11
    r_addr_bits = (r_addr & 0b111) << 8
    reg_data_bits = (r_data & 0b111) << 5
    # offset is 5 bits but is shifted left by 2
    offset_bits = (offset & 0x1F)
    instruction = opcode | r_addr_bits | reg_data_bits | offset_bits
    return [(instruction >> 8) & 0xFF, instruction & 0xFF]

def add_logging_instructions_to_arc_dbg_fw(base_fw_file_path: str,modified_fw_file_path: str, log_context: ArcDfwLogContext) -> None:
    symbol_locations = parse_elf_symbols()
    
    LOG_FUNCITON_EDITABLE = int(symbol_locations["log_function"],16) #+ 0x24

    base_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", base_fw_file_path)
    hex_lines = load_hex_file(base_file_name)
    
    MAX_WRITE_BYTES = 200*4 # enforce this later

    write_bytes = []
    for i,log_info in enumerate(log_context.log_list):
        write_bytes += create_load_instruction(1, log_info.address)
        write_bytes += create_store_instruction(0, 1, i)

    # Loading dfw_buffer_header address so it can be incremented
    write_bytes += create_load_instruction(1, int(symbol_locations["dfw_buffer_header"],16))
    # Incrementing the number of log calls and returning to the main loop    
    # end_address:	     443c                	ld_s	r0,[r1,0x1c]
    # end_address + 0x2: 7104                	add_s	r0,r0,1
    # end_address + 0x4: a107                	st_s	r0,[r1,0x1c]
    # end_address + 0x6: 7ee0                	j_s	[blink]
    write_bytes += [0x44, 0x3c, 0x71, 0x04, 0xa1, 0x07, 0x7e, 0xe0]
    bytes_written = 0
    # Write new instructions to the hex file, because of the endianess 
    for i in range(0, len(write_bytes), 2):
        byte_pair = (write_bytes[i] << 8) | (write_bytes[i + 1] if i + 1 < len(write_bytes) else 0)
        change_two_bytes_at_address(hex_lines, LOG_FUNCITON_EDITABLE + i, byte_pair)
        bytes_written += 2

    save_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", modified_fw_file_path)
    save_hex_file(save_file_name, hex_lines)

    return ""
