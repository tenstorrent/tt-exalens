# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum
from functools import cached_property
import re
from typing import TYPE_CHECKING, Callable

from ttexalens.context import Context
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.device import Device
    from ttexalens.hardware.device_address import DeviceAddress
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
    base_address: DeviceAddress | None = None
    offset: int = 0
    mask: int = 0xFFFFFFFF
    shift: int = 0
    data_type: REGISTER_DATA_TYPE = REGISTER_DATA_TYPE.INT_VALUE

    @property
    def noc_address(self) -> int | None:
        if self.base_address is None or self.base_address.noc_address is None:
            return None
        return self.base_address.noc_address + self.offset

    @property
    def private_address(self) -> int | None:
        if self.base_address is None or self.base_address.private_address is None:
            return None
        return self.base_address.private_address + self.offset

    @property
    def raw_address(self) -> int | None:
        if self.base_address is None or self.base_address.raw_address is None:
            return None
        return self.base_address.raw_address + self.offset

    @property
    def noc_id(self) -> int | None:
        assert self.base_address is not None and self.base_address.noc_address is not None
        return self.base_address.noc_id

    def clone(self, base_address: DeviceAddress) -> "RegisterDescription":
        new_instance = deepcopy(self)
        new_instance.base_address = base_address
        return new_instance

    def change_offset(self, offset: int) -> "RegisterDescription":
        new_instance = deepcopy(self)
        new_instance.offset = self.offset + offset
        return new_instance


@dataclass
class DebugRegisterDescription(RegisterDescription):
    pass


@dataclass
class RiscControlRegisterDescription(RegisterDescription):
    pass


@dataclass
class ConfigurationRegisterDescription(RegisterDescription):
    index: int = 0

    def __post_init__(self):
        self.offset = self.offset + self.index * 4


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
    registers_map: dict[str, RegisterDescription]
    get_register_base_address: Callable[[RegisterDescription], DeviceAddress]


class RegisterStore:
    def __init__(
        self, initialization: RegisterStoreInitialization, location: OnChipCoordinate, neo_id: int | None = None
    ):
        self.registers = initialization.registers_map
        self._get_register_base_address = initialization.get_register_base_address
        self.location = location
        self.neo_id = neo_id

    @property
    def device(self) -> Device:
        return self.location._device

    @property
    def context(self) -> Context:
        return self.device._context

    @cached_property
    def _control_register_address(self) -> int:
        address = self.get_register_noc_address("RISCV_DEBUG_REG_CFGREG_RD_CNTL")
        assert address is not None, "Control register address must be defined."
        return address

    @cached_property
    def _data_register_address(self) -> int:
        address = self.get_register_noc_address("RISCV_DEBUG_REG_CFGREG_RDDATA")
        assert address is not None, "Data register address must be defined."
        return address

    @cached_property
    def _max_config_register_index(self) -> int:
        # TODO: This should be determined by the device's memory map.
        return 1000

    def get_register_names(self) -> list[str]:
        return list(self.registers.keys())

    def get_register_description(self, register_name: str) -> RegisterDescription:
        if register_name in self.registers:
            return self.registers[register_name]
        elif self.neo_id is None:
            raise ValueError(
                f"Unknown register name '{register_name}' on {self.location.to_user_str()} for device {self.device._id}."
            )
        else:
            raise ValueError(
                f"Unknown register name '{register_name}' on {self.location.to_user_str()} [NEO {self.neo_id}] for device {self.device._id}."
            )

    def get_register_noc_address(self, register_name: str) -> int | None:
        register = self.get_register_description(register_name)
        assert register.mask == 0xFFFFFFFF
        return register.noc_address

    def get_register_private_address(self, register_name: str) -> int | None:
        register = self.get_register_description(register_name)
        assert register.mask == 0xFFFFFFFF
        return register.private_address

    def get_register_raw_address(self, register_name: str) -> int | None:
        register = self.get_register_description(register_name)
        assert register.mask == 0xFFFFFFFF
        return register.raw_address

    def parse_register_description(self, input_string: str) -> tuple[RegisterDescription, str]:
        # Check if the input string is a register name
        if input_string in self.registers:
            return self.registers[input_string], input_string

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
            raise ValueError(f"Invalid mask value {mask}. Mask must be between 0 and 0xFFFFFFFF.")
        if shift < 0 or shift > 31:
            raise ValueError(f"Invalid shift value {shift}. Shift must be between 0 and 31.")
        register: RegisterDescription
        if name == "cfg":
            # Configuration register. Parameters: index, mask, shift
            register = ConfigurationRegisterDescription(index=arguments[0], mask=mask, shift=shift)
        elif name == "dbg":
            # Debug register. Parameters: address, mask, shift
            register = DebugRegisterDescription(offset=arguments[0], mask=mask, shift=shift)
        else:
            raise ValueError(f"Unknown register type: {name}. Possible values: [cfg,dbg]")
        register = register.clone(self._get_register_base_address(register))

        if isinstance(register, ConfigurationRegisterDescription):
            max_index = self._max_config_register_index
            if register.index < 0 or register.index > max_index:
                raise ValueError(
                    f"Register index must be positive and less than or equal to {max_index}, but got {register.index}"
                )

        return register, register.__str__()

    def read_register(self, register: str | RegisterDescription) -> int:
        if isinstance(register, str):
            register = self.get_register_description(register)
        else:
            if register.mask < 0 or register.mask > 0xFFFFFFFF:
                raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")
            if register.shift < 0 or register.shift > 31:
                raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")
            if isinstance(register, ConfigurationRegisterDescription):
                if register.index < 0:
                    raise ValueError(f"Register index must be positive, but got {register.index}.")
                if register.index > self._max_config_register_index:
                    raise ValueError(
                        f"Register index must be less than or equal to {self._max_config_register_index}, but got {register.index}."
                    )
            if register.base_address is None:
                register = register.clone(self._get_register_base_address(register))

        if register.noc_address is not None:
            value = read_word_from_device(
                self.location, register.noc_address, self.device._id, self.context, register.noc_id
            )
        elif register.raw_address is not None:
            value = self.context.server_ifc.pci_read32_raw(self.device._id, register.raw_address)
        elif isinstance(register, ConfigurationRegisterDescription):
            write_words_to_device(
                self.location,
                self._control_register_address,
                register.index,
                self.device._id,
                self.context,
            )
            value = read_word_from_device(self.location, self._data_register_address, self.device._id, self.context)
        else:
            # Read using RISC core debugging hardware.
            risc_debug = self.device.get_block(self.location).get_default_risc_debug()
            assert register.private_address is not None, "Register must have a private address for writing."
            with risc_debug.ensure_private_memory_access():
                value = risc_debug.read_memory(register.private_address)
        return (value & register.mask) >> register.shift

    def write_register(self, register: str | RegisterDescription, value: int) -> None:
        if isinstance(register, str):
            register = self.get_register_description(register)
        else:
            if isinstance(register, ConfigurationRegisterDescription):
                register = register.clone(self._get_register_base_address(register))
            if register.mask < 0 or register.mask > 0xFFFFFFFF:
                raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")
            if register.shift < 0 or register.shift > 31:
                raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")
            if isinstance(register, ConfigurationRegisterDescription):
                if register.index < 0:
                    raise ValueError(f"Register index must be positive, but got {register.index}.")
                if register.index > self._max_config_register_index:
                    raise ValueError(
                        f"Register index must be less than or equal to {self._max_config_register_index}, but got {register.index}."
                    )
            if register.base_address is None:
                register = register.clone(self._get_register_base_address(register))
        if value < 0 or ((value << register.shift) & ~register.mask) != 0:
            raise ValueError(
                f"Value must be greater than 0 and inside the mask 0x{register.mask:x}, but got {value} (0x{value:x})"
            )

        if register.noc_address is not None:
            if register.mask != 0xFFFFFFFF:
                old_value = read_word_from_device(
                    self.location, register.noc_address, self.device._id, self.context, register.noc_id
                )
                value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
            write_words_to_device(
                self.location, register.noc_address, value, self.device._id, self.context, register.noc_id
            )
        elif register.raw_address is not None:
            if register.mask != 0xFFFFFFFF:
                old_value = self.context.server_ifc.pci_read32_raw(self.device._id, register.raw_address)
                value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
            self.context.server_ifc.pci_write32_raw(self.device._id, register.raw_address, value)
        else:
            # Write using RISC core debugging hardware.
            risc_debug = self.device.get_block(self.location).get_default_risc_debug()
            assert register.private_address is not None, "Register must have a private address for writing."
            with risc_debug.ensure_private_memory_access():
                if register.mask != 0xFFFFFFFF:
                    old_value = risc_debug.read_memory(register.private_address)
                    value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
                risc_debug.write_memory(register.private_address, value)

    @staticmethod
    def create_initialization(
        register_offset_maps: dict[str, RegisterDescription] | list[dict[str, RegisterDescription]],
        get_register_base_address: Callable[[RegisterDescription], DeviceAddress],
    ) -> RegisterStoreInitialization:
        """
        This method creates an initialization object for register store.
        Idea behind it is to create one initialization object per noc block type
        and then using that object create many register stores that are tied to noc block.
        This way we save initialization time as creating store from initialization object is fast.
        """
        if not isinstance(register_offset_maps, list):
            register_offset_maps = [register_offset_maps]
        register_map = {}
        for register_offset_map in register_offset_maps:
            for register_name, register_description in register_offset_map.items():
                register_map[register_name] = register_description.clone(
                    get_register_base_address(register_description)
                )
        return RegisterStoreInitialization(register_map, get_register_base_address)
