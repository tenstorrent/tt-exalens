#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
'''
Common functionality for register access utilities.

Provides shared functions and settings used by both YAML and JSON register access implementations.
'''
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from tabulate import tabulate, TableFormat, Line, DataRow

# --- Verbosity Settings ---
VERBOSE_MODE = False

def set_verbose(enable: bool) -> None:
    """Enable or disable verbose mode for register operations."""
    global VERBOSE_MODE
    VERBOSE_MODE = enable

def get_verbose() -> bool:
    """Get current verbose mode setting."""
    global VERBOSE_MODE
    return VERBOSE_MODE

def verbose_print(message: str) -> None:
    """Print message if verbose mode is enabled."""
    if VERBOSE_MODE:
        print(f"[REG_ACCESS] {message}")

# Create a custom format with box drawing characters
# Align the table to the left
fancy_pretty = TableFormat(
    lineabove=Line("╭", "─", "┬", "╮"),
    linebelowheader=Line("├", "─", "┼", "┤"),
    linebetweenrows=None,
    linebelow=Line("╰", "─", "┴", "╯"),
    headerrow=DataRow("│", "│", "│"),
    datarow=DataRow("│", "│", "│"),
    padding=1,
    with_header_hide=None
)

DEFAULT_TABLE_FORMAT = fancy_pretty

# --- Mock Register Memory ---
mock_register_memory = {}

def mock_reg_read(addr: int) -> int:
    """Mock read from register memory. Returns LSB 32 bits of address on first read."""
    if addr not in mock_register_memory:
        initial_value = addr & 0xFFFFFFFF
        mock_register_memory[addr] = initial_value # Store as 64-bit int
        verbose_print(f"MOCK_READ[0x{addr:X}] -> 0x{initial_value:X} (first read, initialized to addr & 0xFFFFFFFF)")
        return initial_value
    else:
        value = mock_register_memory[addr]
        verbose_print(f"MOCK_READ[0x{addr:X}] -> 0x{value:X}")
        return value

def mock_reg_write(addr: int, data: int) -> None:
    """Mock write to register memory."""
    # Mask data to 64 bits before storing
    masked_data = data & 0xFFFFFFFFFFFFFFFF
    verbose_print(f"MOCK_WRITE[0x{addr:X}] <- 0x{masked_data:X}")
    mock_register_memory[addr] = masked_data

def clear_mock_memory() -> None:
    """Clear the mock register memory."""
    global mock_register_memory
    old_size = len(mock_register_memory)
    mock_register_memory = {}
    verbose_print(f"Cleared mock register memory ({old_size} entries)")

# --- Base Classes ---

class BaseRegister:
    """Base class for register instances.
    
    Register Access:
        Registers must be accessed using explicit read() and write() methods:
        >>> value = register.read()  # Read register value
        >>> register.write(0x1234)   # Write register value
        
        Direct assignment is not supported:
        >>> value = register         # Returns Register object, not value
        >>> register = 0x1234        # Not supported
    
    Field Access:
        Register fields can be accessed directly as attributes:
        >>> field_value = register.field_name    # Read field
        >>> register.field_name = 1              # Write field
        
        Fields are automatically masked and validated to their bit ranges.
    """
    def __init__(self, reg_def: dict, block_instance: 'BaseRegisterBlock', index: Optional[int] = None):
        self._reg_def = reg_def
        self._block = block_instance
        self._index = index
        self._base_address = self._calculate_base_address()
        self._fields = self._get_fields()

    @abstractmethod
    def _calculate_base_address(self) -> int:
        """Calculate the base address for this register instance."""
        pass

    @abstractmethod
    def _get_fields(self) -> dict:
        """Get the fields dictionary from reg_def."""
        pass

    def read(self) -> int:
        """Reads the full register value."""
        value = self._block.reg_read(self._base_address)
        verbose_print(f"Register READ @ 0x{self._base_address:X} -> 0x{value:X}")
        return value

    def write(self, value: int) -> None:
        """Writes the full register value."""
        verbose_print(f"Register WRITE @ 0x{self._base_address:X} <- 0x{value:X}")
        self._block.reg_write(self._base_address, value)

    def __getattr__(self, name: str):
        """Handle read access to register fields."""
        if name in self._fields:
            field_def = self._fields[name]
            _word_offset, msb, lsb, _description = field_def
            width = msb - lsb + 1
            mask = ((1 << width) - 1)

            full_reg_val = self.read()
            field_value = (full_reg_val >> lsb) & mask
            verbose_print(f"Field READ {name} [bits {msb}:{lsb}] from reg @ 0x{self._base_address:X} -> 0x{field_value:X}")
            return field_value

        verbose_print(f"ERROR: Field '{name}' not found in register @ 0x{self._base_address:X}")
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}' or it's not a defined field. Available fields: {self._fields.keys()}")

    def __setattr__(self, name: str, value) -> None:
        """Handle write access to register fields and regular attributes."""
        if name.startswith('_') or hasattr(type(self), name):
            super().__setattr__(name, value)
        elif hasattr(self, '_fields') and name in self._fields:
            if not isinstance(value, int):
                verbose_print(f"ERROR: Field '{name}' value must be an integer, got {type(value)}")
                raise TypeError(f"Value for field '{name}' must be an integer, got {type(value)}")

            field_def = self._fields[name]
            _word_offset, msb, lsb, _description = field_def
            width = msb - lsb + 1
            field_mask = ((1 << width) - 1)

            max_field_value = (1 << width) - 1
            if value > max_field_value:
                verbose_print(f"ERROR: Field '{name}' value 0x{value:X} exceeds max of 0x{max_field_value:X}")
                raise ValueError(
                    f"Value 0x{value:X} is too large for field '{name}'. "
                    f"Field width is {width} bits (MSB={msb}, LSB={lsb}), "
                    f"maximum value is 0x{max_field_value:X}."
                )

            value &= field_mask
            current_reg_val = self.read()
            register_mask = field_mask << lsb
            cleared_val = current_reg_val & ~register_mask
            new_reg_val = cleared_val | (value << lsb)
            verbose_print(f"Field WRITE {name} [bits {msb}:{lsb}] @ 0x{self._base_address:X} <- 0x{value:X}")
            verbose_print(f"  Register value changing from 0x{current_reg_val:X} to 0x{new_reg_val:X}")
            self.write(new_reg_val)
        else:
            super().__setattr__(name, value)

    def __str__(self):
        """Return a string representation including fields."""
        headers = ["Field Name", "MSB", "LSB", "Description"]
        table = []
        for field_name, field_def in sorted(self._fields.items(), key=lambda item: item[1][2]):
            _word_offset, msb, lsb, *rest = field_def
            description = rest[-1] if rest else ''
            table.append([field_name, msb, lsb, description])

        field_table = tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)
        title = self.__repr__()
        return f"{title}\n{field_table}"

class BaseRegisterArray:
    """Base class for register arrays.
    
    Array Access:
        Array registers are accessed using index notation:
        >>> reg = array[0]          # Get register at index 0
        >>> value = array[1].read() # Read value at index 1
        >>> array[2].write(0x1234)  # Write value at index 2
        
    Field Access:
        For non-array registers, fields can be accessed directly:
        >>> field_value = register.field_name
        >>> register.field_name = 1
        
        For array registers, you must index first:
        >>> field_value = array[0].field_name
        >>> array[1].field_name = 1
    """
    def __init__(self, reg_name: str, reg_def: dict, block_instance: 'BaseRegisterBlock'):
        self._name = reg_name
        self._reg_def = reg_def
        self._block = block_instance
        self._is_array = self._check_is_array()

    @abstractmethod
    def _check_is_array(self) -> bool:
        """Check if this is an array type register."""
        pass

    @abstractmethod
    def _get_array_size(self) -> int:
        """Get the array size from reg_def."""
        pass

    def __getitem__(self, index: int) -> BaseRegister:
        """Access a specific register instance in the array."""
        if not self._is_array:
            raise TypeError(f"Register '{self._name}' is not an array.")
        array_size = self._get_array_size()
        if not 0 <= index < array_size:
            raise IndexError(f"Index {index} out of bounds for {self._name}[{array_size}]")
        return self._create_register_instance(index)

    @abstractmethod
    def _create_register_instance(self, index: Optional[int] = None) -> BaseRegister:
        """Create a register instance."""
        pass

    def __getattr__(self, name: str):
        """Allow direct field access if it's not an array."""
        if self._is_array:
            raise AttributeError(f"Cannot access fields directly on array '{self._name}'. Index first (e.g., {self._name}[0].{name})")
        reg_instance = self._create_register_instance()
        return getattr(reg_instance, name)

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif hasattr(self, '_is_array') and not self._is_array:
            reg_instance = self._create_register_instance()
            setattr(reg_instance, name, value)
        else:
            super().__setattr__(name, value)

    def __str__(self):
        """Return a string representation including fields or array info."""
        title = self.__repr__()
        info = self._get_info_table()
        field_table = self._get_field_table()
        return f"{title}\n{info}\nFields:\n{field_table}"

    def __len__(self) -> int:
        """Return the number of elements in the array."""
        if not self._is_array:
            raise TypeError(f"Register '{self._name}' is not an array.")
        return self._get_array_size()

    @abstractmethod
    def _get_info_table(self) -> str:
        """Get the info table for string representation."""
        pass

    @abstractmethod
    def _get_field_table(self) -> str:
        """Get the field table for string representation."""
        pass

class BaseRegisterBlock:
    """Base class for register blocks.
    
    Register Access:
        Registers and register arrays are accessed as attributes:
        >>> reg = block.REGISTER_NAME           # Get register
        >>> value = block.REGISTER_NAME.read()  # Read register
        >>> block.REGISTER_NAME.write(0x1234)   # Write register
        >>> array_reg = block.ARRAY_NAME[0]     # Get array register
    """
    def __init__(self, block_name: str, block_def: dict, parent_map: 'BaseRegisterMap'):
        self._name = block_name
        self._block_def = block_def
        self._parent = parent_map
        self.base_offset = block_def['offset']
        self.reg_read = parent_map.reg_read
        self.reg_write = parent_map.reg_write
        self._register_data = self._load_register_data()
        self._regsize = self._get_regsize()
        self._cached_registers = {}

    @abstractmethod
    def _load_register_data(self) -> dict:
        """Load register definitions for this block."""
        pass

    @abstractmethod
    def _get_regsize(self) -> int:
        """Get register size for this block."""
        pass

    def __getattr__(self, name: str) -> BaseRegisterArray:
        """Lazy load register definitions."""
        if name in self._cached_registers:
            return self._cached_registers[name]

        if name in self._register_data:
            reg_def = self._register_data[name]
            if isinstance(reg_def, dict):
                instance = self._create_register_array(name, reg_def)
                self._cached_registers[name] = instance
                return instance

        available_registers = self._get_available_registers_info()
        err_msg = f"Register block '{self._name}' has no register definition named '{name}'.\nAvailable registers in this block:\n{available_registers}"
        raise AttributeError(err_msg)

    @abstractmethod
    def _create_register_array(self, name: str, reg_def: dict) -> BaseRegisterArray:
        """Create a register array instance."""
        pass

    def _get_available_registers_info(self) -> str:
        """Returns a tabulated string of available registers in the block."""
        headers = ["Register Name", "Address", "Type", "Size", "Regsize", "Description"]
        table = []
        register_items = self._get_register_items()
        for reg_name, reg_def in sorted(register_items, key=self._get_register_sort_key):
            table.append(self._get_register_info_row(reg_name, reg_def))
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    @abstractmethod
    def _get_register_items(self) -> list:
        """Get list of register items for info table."""
        pass

    @abstractmethod
    def _get_register_sort_key(self, item) -> int:
        """Get sort key for register items."""
        pass

    @abstractmethod
    def _get_register_info_row(self, reg_name: str, reg_def: dict) -> list:
        """Get info row for a register."""
        pass

class BaseRegisterMap:
    """Base class for register maps.
    
    Block Access:
        Register blocks are accessed as attributes:
        >>> block = reg_map.BLOCK_NAME
        
    Register Access Examples:
        >>> value = reg_map.BLOCK.REGISTER.read()       # Read register
        >>> reg_map.BLOCK.REGISTER.write(0x1234)        # Write register
        >>> reg_map.BLOCK.REGISTER.field_name = 1       # Write field
        >>> value = reg_map.BLOCK.ARRAY[0].read()       # Read array register
        >>> reg_map.BLOCK.ARRAY[1].field_name = 1       # Write array register field
    """
    def __init__(self, top_file_path: str, reg_read_func=None, reg_write_func=None):
        self.top_file_path = top_file_path
        self._top_level_data = self._load_top_level_data()
        self.reg_read = reg_read_func if reg_read_func is not None else mock_reg_read
        self.reg_write = reg_write_func if reg_write_func is not None else mock_reg_write
        self._cached_blocks = {}

    @abstractmethod
    def _load_top_level_data(self) -> dict:
        """Load top level register map data."""
        pass

    def __getattr__(self, name: str) -> BaseRegisterBlock:
        """Lazy load register blocks."""
        if name in self._cached_blocks:
            return self._cached_blocks[name]

        if name in self._top_level_data:
            block_def = self._top_level_data[name]
            if self._is_valid_block_def(block_def):
                instance = self._create_register_block(name, block_def)
                self._cached_blocks[name] = instance
                return instance

        available_blocks = self._get_available_blocks_info()
        err_msg = f"Register map has no block definition named '{name}'.\nAvailable blocks:\n{available_blocks}"
        raise AttributeError(err_msg)

    @abstractmethod
    def _is_valid_block_def(self, block_def: dict) -> bool:
        """Check if block definition is valid."""
        pass

    @abstractmethod
    def _create_register_block(self, name: str, block_def: dict) -> BaseRegisterBlock:
        """Create a register block instance."""
        pass

    @abstractmethod
    def _get_available_blocks_info(self) -> str:
        """Returns a tabulated string of available blocks."""
        pass 