# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum
import re
from typing import Callable, Dict, List, Union

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device
from ttexalens.unpack_regfile import TensixDataFormat

# An enumeration of different data types in registers.
class REGISTER_DATA_TYPE(Enum):
    INT_VALUE = 0
    ADDRESS = 1
    MASK = 2
    FLAGS = 3
    TENSIX_DATA_FORMAT = 4


def format_register_value(value: int, data_type: REGISTER_DATA_TYPE, number_of_bits: int):
    if data_type == REGISTER_DATA_TYPE.INT_VALUE:
        return value
    elif data_type == REGISTER_DATA_TYPE.ADDRESS or data_type == REGISTER_DATA_TYPE.MASK:
        return hex(value)
    elif data_type == REGISTER_DATA_TYPE.FLAGS:
        bin_repr = f"{value:0{number_of_bits}b}"
        return ",".join("True" if bit == "1" else "False" for bit in bin_repr)
    elif data_type == REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT:
        try:
            return f"TensixDataFormat.{TensixDataFormat(value).name}"
        except:
            return f"{value} -> INVALID VALUE"
    else:
        raise ValueError(f"Invalid value for data_type: {data_type}")


def parse_register_value(value: str) -> int:
    if re.match(r"^0x[0-9a-fA-F]+$", value):
        return int(value, 16)
    elif re.match(r"^0b[0-1]+$", value):
        return int(value, 2)
    elif re.match(r"^[0-9]+$", value):
        return int(value)
    elif re.match(r"^(True|False)(,(True|False))*$", value):
        return int("".join(["1" if v == "True" else "0" for v in value.split(",")]), 2)
    elif value in TensixDataFormat.__members__:
        return TensixDataFormat[value].value
    else:
        raise ValueError(
            f"Invalid value {value}. Expected a hexadecimal or decimal integer, boolean list or TensixDataFormat."
        )


@dataclass
class RegisterDescription:
    address: int = 0
    mask: int = 0xFFFFFFFF
    shift: int = 0
    data_type: REGISTER_DATA_TYPE = REGISTER_DATA_TYPE.INT_VALUE
    noc_address: Union[int, None] = None

    def clone(self, base_address: int, base_noc_address: Union[int, None]) -> "RegisterDescription":
        new_instance = deepcopy(self)
        new_instance.address += base_address
        if base_noc_address is not None:
            new_instance.noc_address = self.address + base_noc_address
        return new_instance


@dataclass
class DebugRegisterDescription(RegisterDescription):
    def __post_init__(self):
        self.noc_address = self.address


@dataclass
class ConfigurationRegisterDescription(RegisterDescription):
    index: int = 0

    def __post_init__(self):
        self.address = self.address + self.index * 4


@dataclass
class NocStatusRegisterDescription(RegisterDescription):
    pass


@dataclass
class NocConfigurationRegisterDescription(RegisterDescription):
    pass


@dataclass
class NocControlRegisterDescription(RegisterDescription):
    pass


@dataclass
class ArcResetRegisterDescription(RegisterDescription):
    pass


@dataclass
class ArcCsmRegisterDescription(RegisterDescription):
    pass


@dataclass
class ArcRomRegisterDescription(RegisterDescription):
    pass


@dataclass
class RegisterStoreInitialization:
    registers: Dict[str, RegisterDescription]
    get_register_internal_base_address: Callable[[RegisterDescription], int]
    get_register_noc_base_address: Callable[[RegisterDescription], Union[int, None]]


class RegisterStore:
    def __init__(
        self, initialization: RegisterStoreInitialization, location: OnChipCoordinate, neo_id: Union[int, None] = None
    ):
        self.registers = initialization.registers
        self._get_register_internal_address = initialization.get_register_internal_base_address
        self._get_register_noc_address = initialization.get_register_noc_base_address
        self.location = location
        self.neo_id = neo_id

    @property
    def device(self):
        return self.location._device

    def get_register_names(self) -> List[str]:
        return list(self.registers.keys())

    def get_register_description(self, register_name: str) -> RegisterDescription:
        if register_name in self.registers:
            return self.registers[register_name]
        elif self.neo_id is None:
            raise ValueError(
                f"Unknown register name '{register_name}' on {self.location.to_user_str()} for device {self.location._device._id}."
            )
        else:
            raise ValueError(
                f"Unknown register name '{register_name}' on {self.location.to_user_str()} [NEO {self.neo_id}] for device {self.location._device._id}."
            )

    def get_register_noc_address(self, register_name: str) -> Union[int | None]:
        register = self.get_register_description(register_name)
        assert register.mask == 0xFFFFFFFF
        return register.noc_address

    def get_register_internal_address(self, register_name: str) -> int:
        register = self.get_register_description(register_name)
        assert register.mask == 0xFFFFFFFF
        return register.address

    def parse_register_description(self, input_string: str) -> RegisterDescription:
        # Check if the input string is a register name
        if input_string in self.registers:
            return self.registers[input_string]

        # Try to parse the input string as a register description
        match = re.match(r"(\w+)\((.*?)\)", input_string)
        if match:
            name = match.group(1)
            arguments = [int(param.strip(), 0) for param in match.group(2).split(",")]
            if len(arguments) < 1:
                raise ValueError(f"No arguments specified for register descriptiong: {input_string}")
            if len(arguments) > 3:
                raise ValueError(f"Too many arguments for register description: {input_string}")
        else:
            raise ValueError(f"Invalid input string format: {input_string}")

        # Create register description based on the parsed name and arguments
        mask = arguments[1] if len(arguments) > 1 else 0xFFFFFFFF
        shift = arguments[2] if len(arguments) > 2 else 0
        if mask < 0 or mask > 0xFFFFFFFF:
            raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")
        if shift < 0 or shift > 31:
            raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")
        if name == "cfg":
            # Configuration register. Parameters: index, mask, shift
            register = ConfigurationRegisterDescription(index=arguments[0], mask=mask, shift=shift)
            register = register.clone(
                self._get_register_internal_address(register), self._get_register_noc_address(register)
            )
        elif name == "dbg":
            # Debug register. Parameters: address, mask, shift
            register = DebugRegisterDescription(address=arguments[0], mask=mask, shift=shift)
            if register.address < self._get_register_internal_address(register):
                register = register.clone(
                    self._get_register_internal_address(register), self._get_register_noc_address(register)
                )
        else:
            raise ValueError(f"Unknown register type: {name}. Possible values: [cfg,dbg]")

        # TODO: This verification needs to be moved to another class. Either device or preferably a tensix debug class.
        # if isinstance(register, ConfigurationRegisterDescription):
        #     max_index = int(
        #         (
        #             device._get_tensix_register_end_address(register)
        #             - device._get_tensix_register_base_address(register)
        #             + 1
        #         )
        #         / 4
        #         - 1
        #     )
        #     if register.index < 0 or register.index > max_index:
        #         raise ValueError(
        #             f"Register index must be positive and less than or equal to {max_index}, but got {register.index}"
        #         )

        return register

    def read_register(self, register: Union[str, RegisterDescription]) -> int:
        if isinstance(register, str):
            register = self.get_register_description(register)
        else:
            if register.mask < 0 or register.mask > 0xFFFFFFFF:
                raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")
            if register.shift < 0 or register.shift > 31:
                raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")

        if register.noc_address is not None:
            value = read_word_from_device(self.location, register.noc_address, self.device._id, self.device._context)
        elif isinstance(register, ConfigurationRegisterDescription):
            write_words_to_device(
                self.location,
                self.get_register_noc_address("RISCV_DEBUG_REG_CFGREG_RD_CNTL"),
                register.index,
                self.device._id,
                self.device._context,
            )
            value = read_word_from_device(
                self.location,
                self.get_register_noc_address("RISCV_DEBUG_REG_CFGREG_RDDATA"),
                self.device._id,
                self.device._context,
            )
        else:
            risc_names = self.device.get_risc_names_for_location(self.location, self.neo_id)
            if len(risc_names) < 1:
                raise ValueError(
                    f"We don't know how to read this register from the device since it doesn't have a RISC core at {self.location.to_user_str()}."
                )
            risc_debug = self.device.get_risc_debug(self.location, risc_names[0], self.neo_id)
            with risc_debug.ensure_private_memory_access():
                value = risc_debug.read_memory(register.address)
        return (value & register.mask) >> register.shift

    def write_register(self, register: Union[str, RegisterDescription], value: int) -> None:
        if isinstance(register, str):
            register = self.get_register_description(register)
        else:
            if isinstance(register, ConfigurationRegisterDescription):
                register = register.clone(
                    self._get_register_internal_address(register), self._get_register_noc_address(register)
                )
            if register.mask < 0 or register.mask > 0xFFFFFFFF:
                raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")
            if register.shift < 0 or register.shift > 31:
                raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")
        if value < 0 or value > 2 ** bin(register.mask).count("1") - 1:
            raise ValueError(f"Value must be between 0 and {2 ** bin(register.mask).count('1') - 1}, but got {value}")

        if register.noc_address is not None:
            if register.mask != 0xFFFFFFFF:
                old_value = read_word_from_device(
                    self.location, register.noc_address, self.device._id, self.device._context
                )
                value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
            write_words_to_device(self.location, register.noc_address, value, self.device._id, self.device._context)
        else:
            risc_names = self.device.get_risc_names_for_location(self.location, self.neo_id)
            if len(risc_names) < 1:
                raise ValueError(
                    f"We don't know how to read this register from the device since it doesn't have a RISC core at {self.location.to_user_str()}."
                )
            risc_debug = self.device.get_risc_debug(self.location, risc_names[0], self.neo_id)
            with risc_debug.ensure_private_memory_access():
                if register.mask != 0xFFFFFFFF:
                    old_value = risc_debug.read_memory(register.address)
                    value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
                risc_debug.write_memory(register.address, value)

    @staticmethod
    def initialize_register_map(
        register_offset_maps: Union[Dict[str, RegisterDescription], List[Dict[str, RegisterDescription]]],
        get_register_internal_base_address: Callable[[RegisterDescription], int],
        get_register_noc_base_address: Callable[[RegisterDescription], Union[int, None]],
    ) -> RegisterStoreInitialization:
        if not isinstance(register_offset_maps, list):
            register_offset_maps = [register_offset_maps]
        register_map = {}
        for register_offset_map in register_offset_maps:
            for register_name, register_description in register_offset_map.items():
                noc_base_address = get_register_noc_base_address(register_description)
                internal_base_address = get_register_internal_base_address(register_description)
                register_map[register_name] = register_description.clone(internal_base_address, noc_base_address)
        return RegisterStoreInitialization(
            register_map, get_register_internal_base_address, get_register_noc_base_address
        )
