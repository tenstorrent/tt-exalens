# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property
from time import sleep
from typing import Iterable, TYPE_CHECKING

from ttexalens.hardware.noc_block import NocBlock
from ttexalens.tt_exalens_lib import read_word_from_device, read_words_from_device, write_words_to_device

# Constants for better code readability
L1_SAMPLE_SIZE_BYTES = 16  # Each 128-bit sample is 16 bytes
WORD_SIZE_BITS = 32
WORDS_PER_SAMPLE = 4  # 4x32-bit words per 128-bit sample
WAIT_SLEEP_SECONDS = 0.001
SENTINEL_VALUE = 0xDEADBEEF
L1_LOW_MEMORY_SIZE = 1024 * 1024  # 1 MiB - low L1 memory limit for sampling

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.device import Device
    from ttexalens.register_store import RegisterStore


@dataclass
class DebugBusSignalDescription:
    rd_sel: int = 0
    daisy_sel: int = 0
    sig_sel: int = 0
    mask: int = 0xFFFFFFFF


@dataclass
class L1MemReg2:
    """
    Representation of RISCV_DEBUG_REG_DBG_L1_MEM_REG2 fields:
      - reserved (bits 31:13)
      - write_trigger (bit 12)
      - sampling_interval (bits 11:4)
      - write_mode (bits 3:0)
    """

    write_trigger: int = 0
    sampling_interval: int = 2
    write_mode: int = 0

    def encode(self) -> int:
        val = 0
        val |= (self.write_trigger & 0x1) << 12
        val |= (self.sampling_interval & 0xFF) << 4
        val |= self.write_mode & 0xF
        return val

    @classmethod
    def decode(cls, raw: int) -> "L1MemReg2":
        return cls(
            write_trigger=(raw >> 12) & 0x1,
            sampling_interval=(raw >> 4) & 0xFF,
            write_mode=raw & 0xF,
        )


# 128 bit value of sampled group of signals
@dataclass
class SignalGroupSample:
    raw_data: list[int]  # list of 128-bit samples
    signal_store: DebugBusSignalStore
    group_name: str

    def _extract_signal_value(self, signal: DebugBusSignalDescription, index: int) -> int:
        """Helper method to extract the value of a single signal."""
        extracted_value = (self.raw_data[index] >> (WORD_SIZE_BITS * signal.rd_sel)) & 0xFFFFFFFF
        return extracted_value & signal.mask

    def _get_signal_value(self, signal: str) -> list[int]:
        # simple signal
        if signal in self.signal_store.signals:
            signal_desc = self.signal_store.get_signal_description(signal)
            return [self._extract_signal_value(signal_desc[0], i) for i in range(len(self.raw_data))]

        # combined signal
        elif self.signal_store.is_combined_signal(signal):
            combined_signals = self.signal_store.get_signal_description(signal)
            ret = []
            for i in range(len(self.raw_data)):
                value = 0
                for j, part in enumerate(combined_signals):
                    value |= self._extract_signal_value(part, i) << (WORD_SIZE_BITS * j)
                ret.append(self.signal_store._normalize_value(value, combined_signals[0].mask))
            return ret

        else:
            raise ValueError(f"Signal '{signal}' does not exist.")

    def items(self):
        for signal in self.signal_store.group_signals[self.group_name]:
            yield signal, self[signal]

    def keys(self):
        for signal in self.signal_store.group_signals[self.group_name]:
            yield signal

    def __getitem__(self, key: str) -> list[int]:
        """Allows dictionary-like access to signal values."""
        if key not in self.signal_store.group_signals[self.group_name]:
            raise KeyError(f"Signal '{key}' not part of group '{self.group_name}'.")
        return self._get_signal_value(key)


class DebugBusSignalStore:
    def __init__(
        self,
        signals: dict[str, DebugBusSignalDescription],
        group_signals: dict[str, list[str]],
        noc_block: NocBlock,
        neo_id: int | None = None,
    ):
        self.signals = signals
        self.group_signals = group_signals
        self.noc_block = noc_block
        self.neo_id = neo_id

    @cached_property
    def device(self) -> Device:
        return self.noc_block.device

    @cached_property
    def location(self) -> OnChipCoordinate:
        return self.noc_block.location

    @cached_property
    def _register_store(self) -> RegisterStore:
        return self.noc_block.get_register_store(neo_id=self.neo_id)

    def _get_register_address(self, register_name: str, description: str) -> int:
        """Get register address with error handling"""
        address = self._register_store.get_register_noc_address(register_name)
        assert address is not None, f"{description} address not found in register store."
        return address

    @cached_property
    def _control_register_address(self) -> int:
        return self._get_register_address("RISCV_DEBUG_REG_DBG_BUS_CNTL_REG", "Control register")

    @cached_property
    def _data_register_address(self) -> int:
        return self._get_register_address("RISCV_DEBUG_REG_DBG_RD_DATA", "Data register")

    @cached_property
    def _l1_mem_reg0_address(self) -> int:
        return self._get_register_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG0", "L1 memory register 0")

    @cached_property
    def _l1_mem_reg1_address(self) -> int:
        return self._get_register_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG1", "L1 memory register 1")

    @cached_property
    def _l1_mem_reg2_address(self) -> int:
        return self._get_register_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG2", "L1 memory register 2")

    @staticmethod
    def get_signal_groups(
        signal_map: dict[str, DebugBusSignalDescription], group_names: dict[tuple[int, int], str]
    ) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}

        for signal_name, signal_desc in signal_map.items():
            key = (signal_desc.daisy_sel, signal_desc.sig_sel)
            group_key = group_names[key]
            if group_key not in groups:
                groups[group_key] = []

            base_name = signal_name.split("/")[0] if "/" in signal_name else signal_name
            if base_name not in groups[group_key]:
                groups[group_key].append(base_name)

        return groups

    def get_signal_names(self) -> Iterable[str]:
        return self.signals.keys()

    def get_group_names(self) -> Iterable[str]:
        # Get all available group names.
        return self.group_signals.keys()

    def get_signals_in_group(self, group_name: str) -> list[str]:
        # Get all signal names in the specified group.
        if group_name not in self.group_signals:
            raise ValueError(f"Unknown group name '{group_name}'.")
        return self.group_signals[group_name]

    def get_base_signal_name(self, signal_name: str) -> str:
        """Extract base signal name from combined signal names like 'signal/0' or 'signal/1'."""
        return signal_name.split("/")[0] if "/" in signal_name else signal_name

    def get_signal_part_names(self, base_name: str) -> list[str]:
        part_names = []
        counter = 0
        while f"{base_name}/{counter}" in self.get_signal_names():
            part_names.append(f"{base_name}/{counter}")
            counter += 1
        return part_names

    def get_group_for_signal(self, signal: str) -> str:
        for group_name, signals in self.group_signals.items():
            if self.get_base_signal_name(signal) in signals:
                return group_name
        return ""

    def is_combined_signal_part(self, signal_name: str) -> bool:
        """Check if signal name indicates a combined signal part (ends with /number)."""
        return "/" in signal_name

    def _normalize_value(self, value: int, mask: int) -> int:
        """Shift value right to remove trailing zeros from mask"""
        return value >> (mask & -mask).bit_length() - 1

    def _validate_signal_parameters(self, signal: DebugBusSignalDescription) -> None:
        # Validate signal parameters are within expected ranges
        if not (0 <= signal.rd_sel <= 3):
            raise ValueError(f"rd_sel must be between 0 and 3, got {signal.rd_sel}")

        if not (0 <= signal.daisy_sel <= 255):
            raise ValueError(f"daisy_sel must be between 0 and 255, got {signal.daisy_sel}")

        if not (0 <= signal.sig_sel <= 65535):
            raise ValueError(f"sig_sel must be between 0 and 65535, got {signal.sig_sel}")

        if not (0 <= signal.mask <= 0xFFFFFFFF):
            raise ValueError(f"mask must be a valid 32-bit integer, got {signal.mask}")

    def _validate_l1_parameters(self, l1_address: int, samples: int = 1, sampling_interval: int = 2) -> None:
        """Validate L1 sampling parameters and raise appropriate errors."""
        if samples < 1:
            raise ValueError(f"samples must be at least 1, but got {samples}")

        if l1_address % 16 != 0:
            raise ValueError(f"L1 address must be 16-byte aligned, got 0x{l1_address:x}")

        end_address = l1_address + (samples * L1_SAMPLE_SIZE_BYTES) - 1
        if end_address >= L1_LOW_MEMORY_SIZE:
            raise ValueError(f"L1 sampling range 0x{l1_address:x}-0x{end_address:x} exceeds 1 MiB limit")

        if samples > 1 and not (2 <= sampling_interval <= 256):
            raise ValueError(
                f"When samples > 1, sampling_interval must be between 2 and 256, but got {sampling_interval}"
            )

    def is_combined_signal(self, signal_name: str) -> bool:
        # Check if signal_name is a base name for a combined signal (has /0, /1, /2... variants)
        return f"{signal_name}/0" in self.signals

    def get_signal_description(self, signal_name: str) -> list[DebugBusSignalDescription]:
        # First check if exact signal exists
        if signal_name in self.signals:
            return [self.signals[signal_name]]

        # If not found, check if it's a base name for combined signal
        if self.is_combined_signal(signal_name):
            # For combined signals, return list of all signal parts (/0, /1, /2, ...)
            # Return list of DebugBusSignalDescription objects for all parts of the combined signal
            part_names = self.get_signal_part_names(signal_name)
            combined_signals = [self.signals[name] for name in part_names]
            return combined_signals

        # Signal not found - raise error with appropriate context
        neo_context = f" [NEO {self.neo_id}]" if self.neo_id is not None else ""
        raise ValueError(
            f"Unknown signal name '{signal_name}' on {self.location.to_user_str()}{neo_context} for device {self.device._id}."
        )

    def get_signal_group_description(self, group_name: str) -> dict[str, list[DebugBusSignalDescription]]:
        """
        Returns a dictionary with signal names as keys and a list of DebugBusSignalDescription objects as values.
        If the signal is simple, the list will contain only one descriptor.
        If the signal is combined, the list will contain multiple descriptors.
        """
        if group_name not in self.group_signals:
            raise ValueError(f"Unknown group name '{group_name}'.")

        signal_descriptions = {}
        for signal_name in self.group_signals[group_name]:
            # Always return a list of descriptors, whether the signal is simple or complex.
            description = self.get_signal_description(signal_name)
            signal_descriptions[signal_name] = description

        return signal_descriptions

    def read_signal(
        self,
        signal: DebugBusSignalDescription | str,
    ) -> int:
        """Reads a debug signal from the Tensix debug daisychain.

        **Direct Register Read:** Reads a 32-bit signal value directly
        from the debug register. It is possible to read all signals listed
        in the debug_bus_signal_map. For complex signals, only their parts,
        marked with the suffix /number, can be read atomically.

        Parameters
        ----------
        signal : DebugBusSignalDescription | str
            The signal to read. Can be a string (signal name) or a DebugBusSignalDescription object.

        Returns
        -------
        int
            A 32-bit value in direct read mode. The value is masked with `signal.mask` if set.
        """
        if isinstance(signal, str):
            signal_desc = self.get_signal_description(signal)
        elif isinstance(signal, DebugBusSignalDescription):
            # Validate signal parameters if passed as DebugBusSignalDescription
            self._validate_signal_parameters(signal)
            signal_desc = [signal]
        else:
            raise ValueError(f"Invalid signal type: {type(signal)}")

        data = self._read_single_register(signal_desc[0])
        value = data & signal_desc[0].mask

        return self._normalize_value(value, signal_desc[0].mask)

    def _read_single_register(self, signal_part: DebugBusSignalDescription) -> int:
        """Read a single 32-bit register value"""
        en = 1
        config = (en << 29) | (signal_part.rd_sel << 25) | (signal_part.daisy_sel << 16) | (signal_part.sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )
        data = read_word_from_device(self.location, self._data_register_address, self.device._id, self.device._context)
        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)
        return data

    def read_signal_group(
        self,
        signal_group: str,
        l1_address: int,
        samples: int = 1,
        sampling_interval: int = 2,
    ) -> SignalGroupSample:
        """Reads a debug signal group from the Tensix debug daisychain.

        **L1 Sampling:** Captures one or more 128-bit signal samples into L1
        memory and reads the result. Combined signals can be read fully, atomically,
        by specifying only the signal name without the /number suffix.

        Parameters
        ----------
        signal_group : str
            The signal group to read. It is signal group name from `group_names`.
        l1_address : int
            Byte-address in L1 memory for the first 128-bit word. Must be 16-byte aligned.
            Must be within low L1 memory range (0x0 - 0xFFFFF, first 1 MiB). All samples must fit within this range.
        samples : int, default=1
            Number of 128-bit samples to capture. If `samples > 1`, hardware performs repeated sampling.
        sampling_interval : int, default=2
            Interval (in cycles) between consecutive samples when `samples > 1`.
            Should be ≥ 2 due to a known hardware bug that may cause one extra sample if `sampling_period == 1`
            It will try to take a sample every N cycles. If the L1 write interface is available when a sample is scheduled,
            the sample will be captured at that time. If the L1 interface is busy, the system will wait and attempt to take
            the sample again after N cycles. Regardless of L1 availability, the system will still collect a total of c samples,
            but the samples may not be taken from equally spaced points in time.

        Returns
        -------
        int
            The object of SignalGroupSample. The SignalGroupSample object behaves like a dictionary: keys are signal names, and
            values are lists of sampled values for each signal.
        """

        # Validate L1 address alignment and memory range
        self._validate_l1_parameters(l1_address, samples, sampling_interval)

        signal_names = self.get_signals_in_group(signal_group)
        signals = {name: self.get_signal_description(name) for name in signal_names}

        # Configure debug bus and setup L1 registers for sampling
        reg2_addr, reg2_struct = self._setup_l1_sampling_configuration(
            next(iter(signals.values()))[0], l1_address, samples, sampling_interval
        )

        # Execute L1 sampling and wait for completion
        self._execute_l1_sampling(reg2_addr, reg2_struct, l1_address, samples)

        return self._process_l1_samples(l1_address, samples, signal_group)

    def _setup_l1_sampling_configuration(
        self, signal: DebugBusSignalDescription, l1_address: int, samples: int, sampling_interval: int
    ) -> tuple[int, L1MemReg2]:
        """
        Configure debug bus and setup L1 memory registers for sampling
        Relevant documentation:
        - https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/DebugDaisychain.md
        """
        # Write the configuration - select 128 bit word
        en = 1
        config = (en << 29) | (signal.daisy_sel << 16) | (signal.sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )

        # Get L1 register addresses
        reg0_addr = self._l1_mem_reg0_address
        reg1_addr = self._l1_mem_reg1_address
        reg2_addr = self._l1_mem_reg2_address

        # Initialize L1 register structure
        reg2_struct = L1MemReg2(write_trigger=0, sampling_interval=2, write_mode=0)

        # Prepare L1 writing - set initial write mode and reg0
        reg2_struct.write_mode = 0xF
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        reg0_val = (l1_address >> 4) & 0xFFFFFFFF
        write_words_to_device(self.location, reg0_addr, reg0_val, self.device._id, self.device._context)

        # Configure sampling mode based on number of samples
        # Write mode values:
        # 0: Overwrite same L1 address (NOT SUPPORTED - causes issues with wait logic)
        # 1: Increment address by 16 bytes after each sample
        # 4: Hardware-driven sampling mode (auto-set when samples > 1)
        write_mode = 1  # Always use mode 1 (increment address)

        if samples > 1:
            reg1_val = ((l1_address >> 4) + samples) & 0xFFFFFFFF
            write_words_to_device(self.location, reg1_addr, reg1_val, self.device._id, self.device._context)
            reg2_struct.write_mode = 4
            reg2_struct.sampling_interval = sampling_interval - 1
        else:
            reg2_struct.write_mode = write_mode

        # Write final configuration to reg2
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)

        return reg2_addr, reg2_struct

    def _execute_l1_sampling(self, reg2_addr: int, reg2_struct: L1MemReg2, l1_address: int, samples: int) -> None:
        """
        Execute L1 sampling process and wait for completion
        Relevant documentation:
        - https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/DebugDaisychain.md
        """
        # wait for the last memory location to be written to
        wait_addr = l1_address + ((samples - 1) * L1_SAMPLE_SIZE_BYTES)
        # Write sentinel value to all 4 32-bit words in the 128-bit location
        sentinel_words = [SENTINEL_VALUE] * WORDS_PER_SAMPLE
        write_words_to_device(self.location, wait_addr, sentinel_words, self.device._id, self.device._context)

        # instruct to write
        reg2_struct.write_trigger = 1
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        reg2_struct.write_trigger = 0
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)

        # wait for the last memory location to be written to
        while read_word_from_device(self.location, wait_addr, self.device._id, self.device._context) == SENTINEL_VALUE:
            sleep(WAIT_SLEEP_SECONDS)

        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)

    def _process_l1_samples(self, l1_address: int, samples: int, group_name: str) -> SignalGroupSample:
        """Process L1 samples and extract signal data based on signal configuration"""

        def read_128bit_sample(addr: int) -> int:
            """Read 4x32-bit words and combine them into a single 128-bit integer"""
            words = read_words_from_device(self.location, addr, self.device._id, WORDS_PER_SAMPLE, self.device._context)
            return sum((words[i] << (WORD_SIZE_BITS * i)) for i in range(WORDS_PER_SAMPLE))

        # Read all samples and extract the correct portion based on signal type
        sample_values = [read_128bit_sample(l1_address + (i * L1_SAMPLE_SIZE_BYTES)) for i in range(samples)]

        return SignalGroupSample(raw_data=sample_values, signal_store=self, group_name=group_name)
