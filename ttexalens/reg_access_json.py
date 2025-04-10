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
    if not os.path.exists(filepath):
        verbose_print(f"ERROR: JSON file not found: {filepath}")
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    verbose_print(f"Loading JSON file: {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
        verbose_print(f"Loaded JSON data: {type(data)}")
        if isinstance(data, dict):
            verbose_print(f"Top level keys: {list(data.keys())}")
            # Process the data to match our expected structure
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    verbose_print(f"Processing block '{key}':")
                    
                    # Process Fields as register blocks
                    if 'Fields' in value:
                        for reg_name, reg_def in value['Fields'].items():
                            if isinstance(reg_def, dict):
                                # Get the register's address as the block offset
                                block_offset = 0
                                if 'Address' in reg_def and isinstance(reg_def['Address'], dict):
                                    addr_str = reg_def['Address'].get('int', '0x0')
                                    block_offset = int(addr_str, 16)
                                
                                # Create a block entry for each register
                                block_name = reg_name
                                block_def = {
                                    'offset': block_offset,  # Use register's address as block offset
                                    'registers': {}
                                }
                                
                                # If this register has its own Fields, add them as registers
                                if 'Fields' in reg_def:
                                    for sub_reg_name, sub_reg_def in reg_def['Fields'].items():
                                        if isinstance(sub_reg_def, list):  # This is a field definition
                                            block_def['registers'][reg_name] = {
                                                'address': 0,  # Address is now relative to block offset
                                                'description': reg_def.get('Description', ''),
                                                'fields': {sub_reg_name: sub_reg_def}
                                            }
                                        elif isinstance(sub_reg_def, dict):  # This is a sub-register
                                            sub_reg_addr = 0
                                            if 'Address' in sub_reg_def and isinstance(sub_reg_def['Address'], dict):
                                                addr_str = sub_reg_def['Address'].get('int', '0x0')
                                                sub_reg_addr = int(addr_str, 16)
                                            
                                            block_def['registers'][sub_reg_name] = {
                                                'address': sub_reg_addr,
                                                'description': sub_reg_def.get('Description', ''),
                                                'fields': {}
                                            }
                                            # Only add array-related fields if explicitly defined
                                            if 'ArraySize' in sub_reg_def:
                                                block_def['registers'][sub_reg_name]['array_size'] = int(sub_reg_def.get('ArraySize', {}).get('int', '0x1'), 16)
                                                block_def['registers'][sub_reg_name]['address_increment'] = int(sub_reg_def.get('AddressIncrement', {}).get('int', '0x1'), 16)
                                            if 'Fields' in sub_reg_def:
                                                block_def['registers'][sub_reg_name]['fields'] = sub_reg_def['Fields']
                                else:
                                    # Regular register without nested fields
                                    block_def['registers'][reg_name] = {
                                        'address': 0,  # Address is now relative to block offset
                                        'description': reg_def.get('Description', ''),
                                    }
                                    # Only add array-related fields if this is actually an array register
                                    if 'ArraySize' in reg_def:
                                        block_def['registers'][reg_name]['array_size'] = int(reg_def.get('ArraySize', {}).get('int', '0x1'), 16)
                                        block_def['registers'][reg_name]['address_increment'] = int(reg_def.get('AddressIncrement', {}).get('int', '0x1'), 16)
                                
                                processed_data[block_name] = block_def
            
            return processed_data
        return data

class JsonRegister(BaseRegister):
    def _calculate_base_address(self) -> int:
        base_addr = self._block.base_offset + self._reg_def.get('address', 0)
        if self._index is not None:
            # Get the register size in bytes (default to 8 for 64-bit)
            reg_size_bits = self._block._regsize
            reg_size_bytes = reg_size_bits // 8
            # Use either the specified increment or the register size in bytes
            increment = self._reg_def.get('address_increment', reg_size_bytes)
            base_addr += self._index * increment
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
                ["AddressIncrement", hex(self._reg_def.get('address_increment', 0))],
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

class JsonRegisterBlock(BaseRegisterBlock):
    def _load_register_data(self) -> dict:
        data = self._block_def.get('registers', {})
        # Scale address increments by register size
        reg_size_bytes = self._get_regsize() // 8
        for reg_def in data.values():
            if 'address_increment' in reg_def:
                reg_def['address_increment'] *= reg_size_bytes
        return data

    def _get_regsize(self) -> int:
        return self._block_def.get('regsize', 32)  # Default to 32-bit registers

    def _create_register_array(self, name: str, reg_def: dict) -> JsonRegisterArray:
        return JsonRegisterArray(name, reg_def, self)

    def _get_register_items(self) -> list:
        return [(k, v) for k, v in self._register_data.items() if isinstance(v, dict)]

    def _get_register_sort_key(self, item) -> int:
        reg_def = item[1]
        addr = reg_def.get('address')
        if isinstance(addr, int):
            return addr
        return float('inf')

    def _get_register_info_row(self, reg_name: str, reg_def: dict) -> list:
        addr = reg_def.get('address', None)
        addr_str = hex(addr) if addr is not None else "N/A"
        desc = reg_def.get('description', '')
        is_array = 'array_size' in reg_def
        reg_type = "Array" if is_array else "Single"
        size = reg_def.get('array_size', '') if is_array else ''
        return [reg_name, addr_str, reg_type, size, self._regsize, desc]

    def __repr__(self):
        return f"<RegisterBlock {self._name} @ 0x{self.base_offset:X} from {self._parent.top_file_path}>"

class JsonRegisterMap(BaseRegisterMap):
    def _load_top_level_data(self) -> dict:
        return load_json_file(self.top_file_path)

    def _is_valid_block_def(self, block_def: dict) -> bool:
        return isinstance(block_def, dict) and 'offset' in block_def

    def _create_register_block(self, name: str, block_def: dict) -> JsonRegisterBlock:
        return JsonRegisterBlock(name, block_def, self)

    def _get_available_blocks_info(self) -> str:
        headers = ["Block Name", "Offset", "Description"]
        table = []
        for block_name, block_def in sorted(self._top_level_data.items(), key=lambda item: item[1].get('offset', float('inf'))):
            if isinstance(block_def, dict) and 'offset' in block_def:
                offset_str = hex(block_def.get('offset', 0))
                desc = block_def.get('description', '')
                table.append([block_name, offset_str, desc])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __repr__(self):
        return f"<RegisterMap: {self.top_file_path}>" 