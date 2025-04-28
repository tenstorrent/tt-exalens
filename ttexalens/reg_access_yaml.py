#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
'''
Register Read/Write access utility using YAML definitions.

Provides classes for accessing register definitions from YAML files and
performing register read/write operations with field-level access.
'''
import yaml
import os
from functools import lru_cache
from typing import Optional, Dict, Any, Callable
from tabulate import tabulate
from .reg_access_common import (
    set_verbose, get_verbose, verbose_print,
    DEFAULT_TABLE_FORMAT, mock_reg_read, mock_reg_write,
    BaseRegister, BaseRegisterArray, BaseRegisterBlock, BaseRegisterMap
)

# --- Helper to load YAML ---
@lru_cache(maxsize=None) # Cache loaded YAML files
def load_yaml_file(filepath: str):
    if not os.path.exists(filepath):
        verbose_print(f"ERROR: YAML file not found: {filepath}")
        raise FileNotFoundError(f"YAML file not found: {filepath}")
    
    verbose_print(f"Loading YAML file: {filepath}")
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

class YamlRegister(BaseRegister):
    def _calculate_base_address(self) -> int:
        base_addr = self._block.base_offset + self._reg_def.get('Address', 0)
        if self._index is not None:
            increment = self._reg_def.get('AddressIncrement', 0)
            base_addr += self._index * increment
        return base_addr

    def _get_fields(self) -> dict:
        return self._reg_def.get('Fields', {})

    def __repr__(self):
        name = self._reg_def.get('Description', 'Unnamed')
        if self._index is not None:
            return f"<Register {name}[{self._index}] @ 0x{self._base_address:X}>"
        else:
            return f"<Register {name} @ 0x{self._base_address:X}>"

class YamlRegisterArray(BaseRegisterArray):
    def _check_is_array(self) -> bool:
        return 'ArraySize' in self._reg_def

    def _get_array_size(self) -> int:
        return self._reg_def['ArraySize']

    def _create_register_instance(self, index: Optional[int] = None) -> YamlRegister:
        return YamlRegister(self._reg_def, self._block, index)

    def __repr__(self):
        if self._is_array:
            return f"<RegisterArray {self._name}[{self._reg_def['ArraySize']}]>"
        else:
            return f"<Register {self._name}>"

    def _get_info_table(self) -> str:
        if self._is_array:
            info = [
                ["Address", hex(self._reg_def.get('Address', 0))],
                ["ArraySize", self._reg_def.get('ArraySize', 'N/A')],
                ["AddressIncrement", hex(self._reg_def.get('AddressIncrement', 0))],
                ["Description", self._reg_def.get('Description', '')]
            ]
        else:
            info = [
                ["Address", hex(self._reg_def.get('Address', 0))],
                ["Description", self._reg_def.get('Description', '')]
            ]
        return tabulate(info, headers=["Property", "Value"], tablefmt=DEFAULT_TABLE_FORMAT)

    def _get_field_table(self) -> str:
        headers = ["Field Name", "MSB", "LSB", "Description"]
        table = []
        fields = self._reg_def.get('Fields', {})
        for field_name, field_def in sorted(fields.items(), key=lambda item: item[1][2]):
            _word_offset, msb, lsb, description = field_def
            table.append([field_name, msb, lsb, description])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

class YamlRegisterBlock(BaseRegisterBlock):
    def _load_register_data(self) -> dict:
        sub_yaml_path = os.path.join(self._parent.yaml_dir, self._block_def['filename'])
        return load_yaml_file(sub_yaml_path)

    def _get_regsize(self) -> int:
        return self._register_data.get('Regsize', 64)

    def _create_register_array(self, name: str, reg_def: dict) -> YamlRegisterArray:
        return YamlRegisterArray(name, reg_def, self)

    def _get_register_items(self) -> list:
        return [(k, v) for k, v in self._register_data.items() if isinstance(v, dict) and k != 'Regsize']

    def _get_register_sort_key(self, item) -> int:
        reg_def = item[1]
        addr = reg_def.get('Address')
        if isinstance(addr, int):
            return addr
        return float('inf')

    def _get_register_info_row(self, reg_name: str, reg_def: dict) -> list:
        addr = reg_def.get('Address', None)
        addr_str = hex(addr) if addr is not None else "N/A"
        desc = reg_def.get('Description', '')
        is_array = 'ArraySize' in reg_def
        reg_type = "Array" if is_array else "Single"
        size = reg_def.get('ArraySize', '') if is_array else ''
        return [reg_name, addr_str, reg_type, size, self._regsize, desc]

    def __repr__(self):
        return f"<RegisterBlock {self._name} @ 0x{self.base_offset:X} from {self._parent.top_file_path}>"

class YamlRegisterMap(BaseRegisterMap):
    def __init__(self, top_yaml_path: str, reg_read_func=None, reg_write_func=None):
        self.yaml_dir = os.path.dirname(top_yaml_path) or '.'
        super().__init__(top_yaml_path, reg_read_func, reg_write_func)

    def _load_top_level_data(self) -> dict:
        return load_yaml_file(self.top_file_path)

    def _is_valid_block_def(self, block_def: dict) -> bool:
        return isinstance(block_def, dict) and 'offset' in block_def and 'filename' in block_def

    def _create_register_block(self, name: str, block_def: dict) -> YamlRegisterBlock:
        return YamlRegisterBlock(name, block_def, self)

    def _get_available_blocks_info(self) -> str:
        headers = ["Block Name", "Offset", "Filename"]
        table = []
        for block_name, block_def in sorted(self._top_level_data.items(), key=lambda item: item[1].get('offset', float('inf'))):
            if isinstance(block_def, dict) and 'offset' in block_def and 'filename' in block_def:
                offset_str = hex(block_def.get('offset', 0))
                fname = block_def.get('filename', '')
                table.append([block_name, offset_str, fname])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __repr__(self):
        return f"<RegisterMap: {self.top_file_path}>" 