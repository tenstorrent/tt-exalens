#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
'''
Register Read/Write access utility using JSON definitions.

Provides classes for accessing register definitions from JSON files and
performing register read/write operations with field-level access.
'''
import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any, Callable
from tabulate import tabulate
from .reg_access_common import (
    set_verbose, get_verbose, verbose_print,
    DEFAULT_TABLE_FORMAT, mock_reg_read, mock_reg_write,
    BaseRegister, BaseRegisterArray, BaseRegisterBlock, BaseRegisterMap
)

# --- Helper to load JSON ---
@lru_cache(maxsize=None) # Cache loaded JSON files
def load_json_file(filepath: str):
    """Load and process JSON register definitions.
    
    Structure of the JSON:
    - Top level contains system spaces (e.g. arc_ss)
    - System spaces contain Fields which can be:
      - Memory arrays (accessed by word index)
      - Register blocks (containing registers)
    """
    if not os.path.exists(filepath):
        verbose_print(f"ERROR: JSON file not found: {filepath}")
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    verbose_print(f"Loading JSON file: {filepath}")
    with open(filepath, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            # This handles the case where JSON has comments which aren't valid JSON
            # In a real application, you'd want to use a JSON5 parser or similar
            verbose_print(f"ERROR: Invalid JSON in {filepath}: {e}")
            raise
            
        verbose_print(f"Loaded JSON data: {type(data)}")
        
        # Extract the first system space object (like "arc_ss")
        if isinstance(data, dict) and len(data) > 0:
            # Get the first system space
            sys_space_name = next(iter(data))
            sys_space = data[sys_space_name]
            
            verbose_print(f"Processing system space: {sys_space_name}")
            
            # Create our processed data structure
            processed_data = {}
            
            # Process the Fields section, which contains memory arrays and register blocks
            if isinstance(sys_space, dict) and "Fields" in sys_space:
                for block_name, block_def in sys_space["Fields"].items():
                    if not isinstance(block_def, dict):
                        continue
                        
                    # Get base address
                    block_addr = 0
                    if "Address" in block_def and isinstance(block_def["Address"], dict):
                        addr_str = block_def["Address"].get("int", "0x0")
                        block_addr = int(addr_str, 16)
                    
                    # Check if this is a memory array (has ArraySize but no Fields)
                    if "ArraySize" in block_def and "Fields" not in block_def:
                        # Get array size
                        array_size_str = block_def["ArraySize"].get("int", "0x1")
                        array_size = int(array_size_str, 16)
                        
                        # Create memory array definition
                        processed_data[block_name] = {
                            "type": "memory_array",
                            "base_address": block_addr,
                            "size": array_size,
                            "description": block_def.get("Description", "")
                        }
                    
                    # This is a register block
                    elif "Fields" in block_def:
                        registers = {}
                        
                        # Process registers in the block
                        for reg_name, reg_def in block_def["Fields"].items():
                            if not isinstance(reg_def, dict):
                                continue
                                
                            # Get register address
                            reg_addr = 0
                            if "Address" in reg_def and isinstance(reg_def["Address"], dict):
                                addr_str = reg_def["Address"].get("int", "0x0")
                                reg_addr = int(addr_str, 16)
                            
                            # Check if this is a register array
                            is_array = "ArraySize" in reg_def
                            array_size = 0
                            if is_array:
                                size_str = reg_def["ArraySize"].get("int", "0x1")
                                array_size = int(size_str, 16)
                            
                            # Create register definition
                            reg_info = {
                                "address": reg_addr,
                                "description": reg_def.get("Description", ""),
                                "fields": {}
                            }
                            
                            # Add array info if applicable
                            if is_array:
                                reg_info["array_size"] = array_size
                            
                            # Process fields if present
                            if "Fields" in reg_def:
                                for field_name, field_def in reg_def["Fields"].items():
                                    if isinstance(field_def, list) and len(field_def) >= 4:
                                        # Field definition: [word_offset, msb, lsb, description]
                                        reg_info["fields"][field_name] = field_def
                            
                            # Add register to block
                            registers[reg_name] = reg_info
                        
                        # Create register block definition
                        processed_data[block_name] = {
                            "type": "register_block",
                            "base_address": block_addr,
                            "registers": registers,
                            "description": block_def.get("Description", "")
                        }
                    
                    # Other block types can be added here
                    else:
                        verbose_print(f"Unknown block type: {block_name}")
            
            return processed_data
            
        return data

class JsonRegister(BaseRegister):
    def _calculate_base_address(self) -> int:
        base_addr = self._block.base_address + self._reg_def.get('address', 0)
        if self._index is not None:
            # Get the register size in bytes (default to 4 for 32-bit)
            reg_size_bits = self._block._regsize
            reg_size_bytes = reg_size_bits // 8
            # For array indexing, use register size (ignore AddressIncrement as per comment)
            base_addr += self._index * reg_size_bytes
        return base_addr

    def _get_fields(self) -> dict:
        return self._reg_def.get('fields', {})

    def __repr__(self):
        name = self._reg_def.get('description', 'Unnamed')
        if self._index is not None:
            return f"<Register {name}[{self._index}] @ 0x{self._base_address:X}>"
        else:
            return f"<Register {name} @ 0x{self._base_address:X}>"

class JsonRegisterArray(BaseRegisterArray):
    def _check_is_array(self) -> bool:
        return 'array_size' in self._reg_def

    def _get_array_size(self) -> int:
        return self._reg_def['array_size']

    def _create_register_instance(self, index: Optional[int] = None) -> JsonRegister:
        return JsonRegister(self._reg_def, self._block, index)

    def __repr__(self):
        if self._is_array:
            return f"<RegisterArray {self._name}[{self._reg_def['array_size']}]>"
        else:
            return f"<Register {self._name}>"

    def _get_info_table(self) -> str:
        if self._is_array:
            info = [
                ["Address", hex(self._reg_def.get('address', 0))],
                ["ArraySize", self._reg_def.get('array_size', 'N/A')],
                ["Description", self._reg_def.get('description', '')]
            ]
        else:
            info = [
                ["Address", hex(self._reg_def.get('address', 0))],
                ["Description", self._reg_def.get('description', '')]
            ]
        return tabulate(info, headers=["Property", "Value"], tablefmt=DEFAULT_TABLE_FORMAT)

    def _get_field_table(self) -> str:
        headers = ["Field Name", "MSB", "LSB", "Description"]
        table = []
        fields = self._reg_def.get('fields', {})
        for field_name, field_def in sorted(fields.items(), key=lambda item: item[1][2]):
            _word_offset, msb, lsb, description = field_def
            table.append([field_name, msb, lsb, description])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

class JsonRegisterBlock:
    """Register block for JSON register definitions."""
    def __init__(self, name: str, block_def: dict, parent_map: 'JsonRegisterMap'):
        self._name = name
        self._block_def = block_def
        self._parent = parent_map
        self.base_address = block_def['base_address']
        self.reg_read = parent_map.reg_read
        self.reg_write = parent_map.reg_write
        self._regsize = 32  # Default to 32-bit registers
        self._register_data = block_def.get('registers', {})
        self._cached_registers = {}

    def __getattr__(self, name: str) -> JsonRegisterArray:
        """Get register by name."""
        if name in self._cached_registers:
            return self._cached_registers[name]

        if name in self._register_data:
            reg_def = self._register_data[name]
            if isinstance(reg_def, dict):
                instance = JsonRegisterArray(name, reg_def, self)
                self._cached_registers[name] = instance
                return instance

        available_registers = self._get_available_registers_info()
        err_msg = f"Register block '{self._name}' has no register definition named '{name}'.\nAvailable registers in this block:\n{available_registers}"
        raise AttributeError(err_msg)

    def _get_available_registers_info(self) -> str:
        """Get info about available registers."""
        headers = ["Register Name", "Address", "Type", "Size", "Description"]
        table = []
        for reg_name, reg_def in sorted(self._register_data.items(), 
                                       key=lambda item: item[1].get('address', 0)):
            addr = reg_def.get('address', 0)
            addr_str = hex(addr)
            desc = reg_def.get('description', '')
            is_array = 'array_size' in reg_def
            reg_type = "Array" if is_array else "Single"
            size = reg_def.get('array_size', '') if is_array else ''
            table.append([reg_name, addr_str, reg_type, size, desc])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __repr__(self):
        return f"<RegisterBlock {self._name} @ 0x{self.base_address:X}>"

class MemoryArray:
    """Memory array for direct word index access."""
    def __init__(self, name: str, array_def: dict, parent_map: 'JsonRegisterMap'):
        self._name = name
        self._array_def = array_def
        self._parent = parent_map
        self.base_address = array_def['base_address']
        self.size = array_def['size']
        self.reg_read = parent_map.reg_read
        self.reg_write = parent_map.reg_write
        
    def __getitem__(self, index):
        """Access memory by word index."""
        if not isinstance(index, int):
            raise TypeError(f"Memory array index must be an integer, got {type(index)}")
            
        if not 0 <= index < self.size:
            raise IndexError(f"Memory array index {index} out of bounds (0 to {self.size-1})")
            
        # Calculate address - word index directly translates to word address
        # (ignoring AddressIncrement as per comment)
        addr = self.base_address + (index * 4)  # Assuming 32-bit words = 4 bytes
        
        # Create a simple register-like object
        class MemoryElement:
            def __init__(self, addr, read_func, write_func):
                self.address = addr
                self._read = read_func
                self._write = write_func
                
            def read(self):
                return self._read(self.address)
                
            def write(self, value):
                return self._write(self.address, value)
                
            def __repr__(self):
                return f"<MemoryElement @ 0x{self.address:X}>"
                
        return MemoryElement(addr, self.reg_read, self.reg_write)
        
    def __repr__(self):
        desc = self._array_def.get('description', '')
        return f"<MemoryArray {self._name}[{self.size}] @ 0x{self.base_address:X} - {desc}>"

class JsonRegisterMap:
    """Register map for JSON register definitions."""
    def __init__(self, top_file_path: str, reg_read_func=None, reg_write_func=None):
        self.top_file_path = top_file_path
        self._top_level_data = load_json_file(self.top_file_path)
        self.reg_read = reg_read_func if reg_read_func is not None else mock_reg_read
        self.reg_write = reg_write_func if reg_write_func is not None else mock_reg_write
        verbose_print(f"Using {'custom' if reg_read_func else 'mock'} read function")
        verbose_print(f"Using {'custom' if reg_write_func else 'mock'} write function")
        self._cached_blocks = {}

    def __getattr__(self, name: str):
        """Get block or memory array by name."""
        if name in self._cached_blocks:
            return self._cached_blocks[name]

        if name in self._top_level_data:
            block_def = self._top_level_data[name]
            
            # Determine block type and create appropriate instance
            block_type = block_def.get('type')
            
            if block_type == 'memory_array':
                instance = MemoryArray(name, block_def, self)
            elif block_type == 'register_block':
                instance = JsonRegisterBlock(name, block_def, self)
            else:
                raise ValueError(f"Unknown block type: {block_type}")
                
            self._cached_blocks[name] = instance
            return instance

        available_blocks = self._get_available_blocks_info()
        err_msg = f"Register map has no block definition named '{name}'.\nAvailable blocks:\n{available_blocks}"
        raise AttributeError(err_msg)

    def _get_available_blocks_info(self) -> str:
        """Get info about available blocks."""
        headers = ["Block Name", "Type", "Base Address", "Description"]
        table = []
        
        for block_name, block_def in sorted(self._top_level_data.items(), 
                                          key=lambda item: item[1].get('base_address', 0)):
            block_type = block_def.get('type', 'Unknown')
            base_addr = block_def.get('base_address', 0)
            addr_str = hex(base_addr)
            desc = block_def.get('description', '')
            table.append([block_name, block_type, addr_str, desc])
            
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __repr__(self):
        return f"<RegisterMap: {self.top_file_path}>" 