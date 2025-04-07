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

# --- Helper to load YAML ---
@lru_cache(maxsize=None) # Cache loaded YAML files
def load_yaml_file(filepath: str):
    if not os.path.exists(filepath):
        verbose_print(f"ERROR: YAML file not found: {filepath}")
        raise FileNotFoundError(f"YAML file not found: {filepath}")
    
    verbose_print(f"Loading YAML file: {filepath}")
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

# --- Register Instance ---
class Register:
    def __init__(self, reg_def, block_instance, index: Optional[int] = None):
        self._reg_def = reg_def # The dictionary defining the register/array
        self._block = block_instance # The parent RegisterBlock
        self._index = index     # Index if part of an array, else None

        # Pre-calculate the base address for this specific register instance
        self._base_address = self._block.base_offset + self._reg_def.get('Address', 0)
        if self._index is not None:
            increment = self._reg_def.get('AddressIncrement', 0)
            self._base_address += self._index * increment
            
        verbose_print(f"Created Register instance at address 0x{self._base_address:X}")

        # Store field definitions
        self._fields = self._reg_def.get('Fields', {})

    def read(self) -> int:
        """Reads the full 64-bit register value."""
        # Assuming Regsize matches the read/write function width (64-bit)
        value = self._block.reg_read(self._base_address)
        verbose_print(f"Register READ @ 0x{self._base_address:X} -> 0x{value:X}")
        return value

    def write(self, value: int) -> None:
        """Writes the full 64-bit register value."""
        # Assuming Regsize matches the read/write function width (64-bit)
        verbose_print(f"Register WRITE @ 0x{self._base_address:X} <- 0x{value:X}")
        self._block.reg_write(self._base_address, value)

    def __getattr__(self, name: str):
        """Handle read access to register fields."""
        if name in self._fields:
            # Field access: perform read and extract field value
            field_def = self._fields[name]
            # field_def: [word_offset, msb, lsb, description]
            _word_offset, msb, lsb, _description = field_def
            width = msb - lsb + 1
            mask = ((1 << width) - 1)

            full_reg_val = self.read()
            field_value = (full_reg_val >> lsb) & mask
            verbose_print(f"Field READ {name} [bits {msb}:{lsb}] from reg @ 0x{self._base_address:X} -> 0x{field_value:X}")
            return field_value

        # If not a field, raise standard AttributeError
        # Note: Access to methods like read will not go through __getattr__
        verbose_print(f"ERROR: Field '{name}' not found in register @ 0x{self._base_address:X}")
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}' or it's not a defined field")

    def __setattr__(self, name: str, value) -> None:
        """Handle write access to register fields and regular attributes."""
        # Handle internal attributes/methods defined directly on the class first
        if name.startswith('_') or hasattr(type(self), name):
            super().__setattr__(name, value)
        elif name in self._fields:
            # Field access: perform read-modify-write
            if not isinstance(value, int):
                verbose_print(f"ERROR: Field '{name}' value must be an integer, got {type(value)}")
                raise TypeError(f"Value for field '{name}' must be an integer, got {type(value)}")

            field_def = self._fields[name]
            _word_offset, msb, lsb, _description = field_def
            width = msb - lsb + 1
            field_mask = ((1 << width) - 1)

            # Check if the value exceeds the field width *before* masking
            max_field_value = (1 << width) - 1
            if value > max_field_value:
                verbose_print(f"ERROR: Field '{name}' value 0x{value:X} exceeds max of 0x{max_field_value:X}")
                raise ValueError(
                    f"Value 0x{value:X} is too large for field '{name}'. "
                    f"Field width is {width} bits (MSB={msb}, LSB={lsb}), "
                    f"maximum value is 0x{max_field_value:X}."
                )

            # Ensure value fits within the field width (this should be redundant now if check passes, but safe to keep)
            value &= field_mask

            current_reg_val = self.read()
            register_mask = field_mask << lsb
            cleared_val = current_reg_val & ~register_mask
            new_reg_val = cleared_val | (value << lsb)
            verbose_print(f"Field WRITE {name} [bits {msb}:{lsb}] @ 0x{self._base_address:X} <- 0x{value:X}")
            verbose_print(f"  Register value changing from 0x{current_reg_val:X} to 0x{new_reg_val:X}")
            self.write(new_reg_val)
        else:
            # If it's not a field or an internal attribute, treat as regular attribute setting
            # Although usually we'd raise AttributeError for undefined attributes
            super().__setattr__(name, value)

    def __repr__(self):
        name = self._reg_def.get('Description', 'Unnamed')
        if self._index is not None:
            return f"<Register {name}[{self._index}] @ 0x{self._base_address:X}>"
        else:
            return f"<Register {name} @ 0x{self._base_address:X}>"

    def __str__(self):
        """Return a string representation including fields."""
        headers = ["Field Name", "MSB", "LSB", "Description"]
        table = []
        # Sort fields by LSB for consistent output
        for field_name, field_def in sorted(self._fields.items(), key=lambda item: item[1][2]): # Sort by LSB (index 2 in field_def)
            _word_offset, msb, lsb, description = field_def
            table.append([field_name, msb, lsb, description])

        field_table = tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)
        title = self.__repr__() # Use repr for the title
        return f"{title}\n{field_table}"

# --- Register Array/Single Register Definition ---
class RegisterArray:
    def __init__(self, reg_name: str, reg_def: dict, block_instance):
        self._name = reg_name
        self._reg_def = reg_def
        self._block = block_instance
        self._is_array = 'ArraySize' in self._reg_def

    def __getitem__(self, index: int) -> Register:
        """Access a specific register instance in the array."""
        if not self._is_array:
            raise TypeError(f"Register '{self._name}' is not an array.")
        array_size = self._reg_def['ArraySize']
        if not 0 <= index < array_size:
            raise IndexError(f"Index {index} out of bounds for {self._name}[{array_size}]")
        # Return a Register instance representing this specific element
        return Register(self._reg_def, self._block, index)

    def __getattr__(self, name: str):
        """Allow direct field access if it's *not* an array."""
        if self._is_array:
            raise AttributeError(f"Cannot access fields directly on array '{self._name}'. Index first (e.g., {self._name}[0].{name})")
        # Create a Register instance for the single register (index=None)
        reg_instance = Register(self._reg_def, self._block, index=None)
        # Now delegate the attribute access to the Register instance
        return getattr(reg_instance, name)

    def __setattr__(self, name, value):
        # Handle internal attributes normally
        if name.startswith('_'):
            super().__setattr__(name, value)
        # Allow setting fields directly if not an array
        elif not self._is_array:
             reg_instance = Register(self._reg_def, self._block, index=None)
             setattr(reg_instance, name, value) # Delegate to Register.__setattr__ via the descriptor
        else:
            raise AttributeError(f"Cannot set fields directly on array '{self._name}'. Index first (e.g., {self._name}[0].{name} = value)")

    def __repr__(self):
        if self._is_array:
             return f"<RegisterArray {self._name}[{self._reg_def['ArraySize']}]>"
        else:
             return f"<Register {self._name}>"

    def __str__(self):
        """Return a string representation including fields or array info."""
        if self._is_array:
            info = [
                ["Address", hex(self._reg_def.get('Address', 0))],
                ["ArraySize", self._reg_def.get('ArraySize', 'N/A')],
                ["AddressIncrement", hex(self._reg_def.get('AddressIncrement', 0))],
                ["Description", self._reg_def.get('Description', '')]
            ]
            info_table = tabulate(info, headers=["Property", "Value"], tablefmt=DEFAULT_TABLE_FORMAT)
        else: # Single Register
            info = [
                ["Address", hex(self._reg_def.get('Address', 0))],
                ["Description", self._reg_def.get('Description', '')]
            ]
            info_table = tabulate(info, headers=["Property", "Value"], tablefmt=DEFAULT_TABLE_FORMAT)

        headers = ["Field Name", "MSB", "LSB", "Description"]
        table = []
        fields = self._reg_def.get('Fields', {})
        # Sort fields by LSB
        for field_name, field_def in sorted(fields.items(), key=lambda item: item[1][2]): # Sort by LSB (index 2 in field_def)
            _word_offset, msb, lsb, description = field_def
            table.append([field_name, msb, lsb, description])
        field_table = tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

        title = self.__repr__() # Use repr for the title
        return f"{title}\n{info_table}\nFields:\n{field_table}"

# --- Register Block ---
class RegisterBlock:
    def __init__(self, block_name: str, block_def: dict, parent_map):
        self._name = block_name
        self._block_def = block_def
        self._parent = parent_map
        self.base_offset = block_def['offset']
        self.reg_read = parent_map.reg_read # Pass down read/write functions
        self.reg_write = parent_map.reg_write

        verbose_print(f"Created RegisterBlock '{block_name}' with base offset 0x{self.base_offset:X}")

        # Load the sub-yaml file
        sub_yaml_path = os.path.join(parent_map.yaml_dir, block_def['filename'])
        self._register_data = load_yaml_file(sub_yaml_path)
        self._regsize = self._register_data.get('Regsize', 64) # Default to 64 if not specified
        verbose_print(f"RegisterBlock '{block_name}' using regsize {self._regsize}")

        # We could pre-populate attributes, but lazy loading via __getattr__ is fine
        self._cached_registers = {}

    def __getattr__(self, name: str) -> RegisterArray:
        """Lazy load register definitions from the sub-yaml."""
        if name in self._cached_registers:
            return self._cached_registers[name]

        # Look for the register definition in the loaded sub-yaml data
        # Skip metadata like 'Regsize'
        if name == 'Regsize':
             raise AttributeError # Or return self._regsize if desired

        if name in self._register_data:
            reg_def = self._register_data[name]
            if isinstance(reg_def, dict): # Check if it looks like a register definition
                 instance = RegisterArray(name, reg_def, self)
                 self._cached_registers[name] = instance
                 return instance

        # If attribute not found, show available registers
        available_registers = self._get_available_registers_info()
        err_msg = f"Register block '{self._name}' has no register definition named '{name}'.\nAvailable registers in this block:\n{available_registers}"
        raise AttributeError(err_msg)

    def __repr__(self):
        return f"<RegisterBlock {self._name} @ 0x{self.base_offset:X} from {self._parent.top_yaml_path}>"

    def _get_available_registers_info(self):
        """Returns a tabulated string of available registers in the block."""
        headers = ["Register Name", "Address", "Type", "Size", "Regsize", "Description"]
        table = []
        # Sort registers by Address value
        def get_address(item):
            reg_def = item[1]
            # Handle cases where Address might be missing or not an int
            addr = reg_def.get('Address')
            if isinstance(addr, int):
                return addr
            return float('inf') # Put registers without a valid address last

        # Filter out non-dictionary items and metadata like 'Regsize' before sorting
        register_items = [(k, v) for k, v in self._register_data.items() if isinstance(v, dict) and k != 'Regsize']

        for reg_name, reg_def in sorted(register_items, key=get_address):
            addr = reg_def.get('Address', None)
            addr_str = hex(addr) if addr is not None else "N/A"
            desc = reg_def.get('Description', '')
            is_array = 'ArraySize' in reg_def
            reg_type = "Array" if is_array else "Single"
            size = reg_def.get('ArraySize', '') if is_array else ''
            # Get regsize from the block's _regsize attribute
            regsize = self._regsize
            table.append([reg_name, addr_str, reg_type, size, regsize, desc])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __str__(self):
        """Return a string representation including available registers."""
        title = self.__repr__()
        available_registers = self._get_available_registers_info()
        return f"{title}\n{available_registers}"

# --- Top Level Map ---
class RegisterMap:
    def __init__(self, top_yaml_path: str, reg_read_func=None, reg_write_func=None):
        """Initialize a RegisterMap from a top-level YAML file.
        
        Args:
            top_yaml_path: Path to the top-level YAML file defining register blocks
            reg_read_func: Function to read a register (addr -> value)
            reg_write_func: Function to write a register (addr, value -> None)
        """
        verbose_print(f"Initializing RegisterMap from {top_yaml_path}")
        self.yaml_dir = os.path.dirname(top_yaml_path) or '.' # Directory of the top yaml
        self.top_yaml_path = top_yaml_path
        self._top_level_data = load_yaml_file(top_yaml_path)
        
        # Use provided functions or fallback to mock implementations
        self.reg_read = reg_read_func if reg_read_func is not None else mock_reg_read
        self.reg_write = reg_write_func if reg_write_func is not None else mock_reg_write
        
        verbose_print(f"Using {'custom' if reg_read_func else 'mock'} read function")
        verbose_print(f"Using {'custom' if reg_write_func else 'mock'} write function")
        
        self._cached_blocks = {}

    def __getattr__(self, name: str) -> RegisterBlock:
        """Lazy load register blocks."""
        if name in self._cached_blocks:
            return self._cached_blocks[name]

        if name in self._top_level_data:
            block_def = self._top_level_data[name]
            if isinstance(block_def, dict) and 'offset' in block_def and 'filename' in block_def:
                 instance = RegisterBlock(name, block_def, self)
                 self._cached_blocks[name] = instance
                 return instance

        # If attribute not found, show available blocks
        available_blocks = self._get_available_blocks_info()
        err_msg = f"Register map has no block definition named '{name}'.\nAvailable blocks:\n{available_blocks}"
        raise AttributeError(err_msg)

    def __repr__(self):
        return f"<RegisterMap: {self.top_yaml_path}>"

    def _get_available_blocks_info(self):
        """Returns a tabulated string of available blocks."""
        headers = ["Block Name", "Offset", "Filename"]
        table = []
        # Sort blocks by offset value
        def get_offset(item):
            block_def = item[1]
            return block_def.get('offset', float('inf')) # Put blocks without offset last

        for block_name, block_def in sorted(self._top_level_data.items(), key=get_offset):
             if isinstance(block_def, dict) and 'offset' in block_def and 'filename' in block_def:
                  offset_str = hex(block_def.get('offset', 0))
                  fname = block_def.get('filename', '')
                  table.append([block_name, offset_str, fname])
        return tabulate(table, headers=headers, tablefmt=DEFAULT_TABLE_FORMAT)

    def __str__(self):
        """Return a string representation including available blocks."""
        title = self.__repr__()
        available_blocks = self._get_available_blocks_info()
        return f"{title}\n{available_blocks}"

# Convenience function to create a RegisterMap instance
def create_register_map(yaml_path: str, 
                        reg_read_func: Optional[Callable[[int], int]] = None, 
                        reg_write_func: Optional[Callable[[int, int], None]] = None,
                        verbose: bool = False) -> RegisterMap:
    """
    Create a RegisterMap instance from a YAML file path.
    
    Args:
        yaml_path: Path to the top-level YAML file.
        reg_read_func: Optional function to read registers (defaults to mock function).
        reg_write_func: Optional function to write registers (defaults to mock function).
        verbose: Enable verbose logging of register operations.
        
    Returns:
        A RegisterMap instance initialized with the provided YAML and functions.
    """
    # Set verbosity before creating the map
    set_verbose(verbose)
    
    return RegisterMap(yaml_path, reg_read_func, reg_write_func) 