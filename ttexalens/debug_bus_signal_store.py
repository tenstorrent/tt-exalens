# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property, cache
from time import sleep
from typing import Iterable, TYPE_CHECKING

from ttexalens.hardware.noc_block import NocBlock
from ttexalens.tt_exalens_lib import read_word_from_device, read_words_from_device, write_words_to_device

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.device import Device
    from ttexalens.register_store import RegisterStore

# Constants for better code readability
WORD_SIZE_BITS = 32
WAIT_SLEEP_SECONDS = 0.001
SENTINEL_VALUE = 0xDEADBEEF


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

    def items(self) -> Iterable[tuple[str, list[int]]]:
        """Returns (signal_name, list of sampled values) pairs."""
        for signal in self.signal_store.debug_bus_signals.signal_groups[self.group_name]:
            yield signal, self[signal]

    def keys(self) -> Iterable[str]:
        """Returns signal names in the group."""
        for signal in self.signal_store.debug_bus_signals.signal_groups[self.group_name]:
            yield signal

    def __getitem__(self, key: str) -> list[int]:
        """For the given signal name in the group, returns a list of sampled values."""
        group = self.signal_store.debug_bus_signals.signal_groups[self.group_name]
        if key not in group:
            raise ValueError(f"Signal '{key}' does not exist in group '{self.group_name}'.")

        mask = group[key]
        return [self.signal_store._normalize_value(sample & mask, mask) for sample in self.raw_data]


class DebugBusSignals:
    def __init__(
        self,
        group_map: dict[str, tuple[int, int]],
        signals: dict[str, DebugBusSignalDescription],
    ):
        self.group_map = group_map
        self.signals = signals
        self.signal_groups: dict[str, dict[str, int]] = self.create_signal_groups(signals)

    def get_base_signal_name(self, signal_name: str) -> str:
        """Extract base signal name from combined signal names like 'signal/0' or 'signal/1'."""
        return signal_name.split("/")[0] if "/" in signal_name else signal_name

    def get_signal_part_names(self, base_name: str) -> list[str]:
        """Get all part names for a combined signal based on its base name."""
        if not self.is_combined_signal(base_name):
            return [base_name]

        part_names = []
        counter = 0
        while f"{base_name}/{counter}" in self.signal_names:
            part_names.append(f"{base_name}/{counter}")
            counter += 1

        return part_names

    def get_group_for_signal(self, signal: str) -> str:
        """Get the group name for a given signal name."""
        for group_name, group_dict in self.signal_groups.items():
            if self.get_base_signal_name(signal) in group_dict:
                return group_name

        return ""

    def is_signal_part(self, signal_name: str) -> bool:
        """Check if signal name indicates a combined signal part (ends with '/number')."""
        return "/" in signal_name

    def is_combined_signal(self, signal_name: str) -> bool:
        """Check if signal name is a base name for a combined signal (has /0, /1, /2... variants)."""
        return f"{signal_name}/0" in self.signals

    @cache
    def get_signal_names_in_group(self, group_name: str) -> Iterable[str]:
        """Get all signal names in the specified group."""
        if group_name not in self.signal_groups:
            raise ValueError(f"Unknown group name '{group_name}'.")

        return self.signal_groups[group_name].keys()

    @cached_property
    def signal_names(self) -> Iterable[str]:
        """Get all signal names."""
        return self.signals.keys()

    @cached_property
    def group_names(self) -> list[str]:
        """Get all group names."""
        return list(self.group_map.keys())

    @cached_property
    def signal_groups(self) -> dict[str, dict[str, int]]:
        """Returns a dict mapping group names to dicts of signal names and their 128-bit masks in that group."""
        return self.signal_groups

    def create_signal_groups(self, signals: dict[str, DebugBusSignalDescription]) -> dict[str, dict[str, int]]:
        """Returns a dict mapping group names to dicts of signal names and their 128-bit masks in that group."""
        groups: dict[str, dict[str, int]] = {}
        for group_key, (daisy_sel, sig_sel) in self.group_map.items():
            group_dict: dict[str, int] = {}
            for signal_name, signal_desc in signals.items():
                if signal_desc.daisy_sel != daisy_sel or signal_desc.sig_sel != sig_sel:
                    continue

                base_name = self.get_base_signal_name(signal_name)
                if base_name in group_dict:
                    continue

                part_names = self.get_signal_part_names(base_name)
                mask = 0
                for part_name in part_names:
                    part_desc = self.get_signal_description(part_name)
                    mask |= part_desc.mask << (WORD_SIZE_BITS * part_desc.rd_sel)

                group_dict[base_name] = mask
            groups[group_key] = group_dict
        return groups

    def get_signal_description(self, signal_name: str) -> DebugBusSignalDescription:
        """Returns the DebugBusSignalDescription for the given signal name."""
        if signal_name in self.signals:
            return self.signals[signal_name]
        raise ValueError(f"Unknown signal name '{signal_name}'.")


class DebugBusSignalStore:
    def __init__(
        self,
        debug_bus_signals: DebugBusSignals,
        noc_block: NocBlock,
        neo_id: int | None = None,
    ):
        self.debug_bus_signals = debug_bus_signals
        self.noc_block = noc_block
        self.neo_id = neo_id
        self.L1_SAMPLE_SIZE_BYTES = 16  # Each 128-bit sample is 16 bytes
        self.WORDS_PER_SAMPLE = 4  # 4x32-bit words per 128-bit sample
        self.L1_LOW_MEMORY_SIZE = 1024 * 1024  # 1 MiB - low L1 memory limit for sampling

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

    def _normalize_value(self, value: int, mask: int) -> int:
        """Shift value right to remove trailing zeros from mask"""
        return value >> (mask & -mask).bit_length() - 1

    def _validate_signal_parameters(self, signal: DebugBusSignalDescription) -> None:
        """Validate signal parameters and raise appropriate errors."""
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

        end_address = l1_address + (samples * self.L1_SAMPLE_SIZE_BYTES) - 1
        if end_address >= self.L1_LOW_MEMORY_SIZE:
            raise ValueError(f"L1 sampling range 0x{l1_address:x}-0x{end_address:x} exceeds 1 MiB limit")

        if samples > 1 and not (2 <= sampling_interval <= 256):
            raise ValueError(
                f"When samples > 1, sampling_interval must be between 2 and 256, but got {sampling_interval}"
            )

    def get_signal_description(self, signal_name: str) -> DebugBusSignalDescription:
        """Returns the DebugBusSignalDescription for the given signal name."""
        signal_desc = self.debug_bus_signals.get_signal_description(signal_name)
        if signal_desc:
            return signal_desc
        elif self.neo_id is None:
            raise ValueError(
                f"Unknown signal name '{signal_name}' on {self.location.to_user_str()} for device {self.device._id}."
            )
        else:
            raise ValueError(
                f"Unknown signal name '{signal_name}' on {self.location.to_user_str()} [NEO {self.neo_id}] for device {self.device._id}."
            )

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
        signal_desc = None
        if isinstance(signal, str):
            signal_desc = self.get_signal_description(signal)
        elif isinstance(signal, DebugBusSignalDescription):
            self._validate_signal_parameters(signal)
            signal_desc = signal
        else:
            raise ValueError(f"Invalid signal type: {type(signal)}")

        data = self._read_single_register(signal_desc)
        value = data & signal_desc.mask

        return self._normalize_value(value, signal_desc.mask)

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

        # Configure debug bus and setup L1 registers for sampling. Took first signal in the group just for daisy/sig selection.
        reg2_addr, reg2_struct = self._setup_l1_sampling_configuration(
            signal_group, l1_address, samples, sampling_interval
        )

        # Execute L1 sampling and wait for completion
        self._execute_l1_sampling(reg2_addr, reg2_struct, l1_address, samples)

        return self._process_l1_samples(l1_address, samples, signal_group)

    def _setup_l1_sampling_configuration(
        self, signal_group: str, l1_address: int, samples: int, sampling_interval: int
    ) -> tuple[int, L1MemReg2]:
        """
        Configure debug bus and setup L1 memory registers for sampling
        Relevant documentation:
        - https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/DebugDaisychain.md
        """
        # get daisy and sig selection for group
        print("PROSLOOOOOOOOOOO", self.debug_bus_signals.group_map)

        daisy_sel, sig_sel = self.debug_bus_signals.group_map[signal_group]

        # Write the configuration - select 128 bit word
        en = 1
        config = (en << 29) | (daisy_sel << 16) | sig_sel
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
        wait_addr = l1_address + ((samples - 1) * self.L1_SAMPLE_SIZE_BYTES)
        # Write sentinel value to all 4 32-bit words in the 128-bit location
        sentinel_words = [SENTINEL_VALUE] * self.WORDS_PER_SAMPLE
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
            words = read_words_from_device(
                self.location, addr, self.device._id, self.WORDS_PER_SAMPLE, self.device._context
            )
            return sum((words[i] << (WORD_SIZE_BITS * i)) for i in range(self.WORDS_PER_SAMPLE))

        # Read samples from L1 memory
        sample_values = [read_128bit_sample(l1_address + (i * self.L1_SAMPLE_SIZE_BYTES)) for i in range(samples)]

        return SignalGroupSample(raw_data=sample_values, signal_store=self, group_name=group_name)
