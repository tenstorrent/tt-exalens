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


# Represents shift and mask for a signal in a group
@dataclass
class ShiftMask:
    shift: int
    mask: int


# 128 bit value of sampled group of signals
@dataclass
class SignalGroupSample:
    def __init__(
        self,
        raw_data: int,
        group: dict[str, ShiftMask],
    ):
        self.raw_data = raw_data  # 128-bit sample
        self.group = group

    def items(self) -> Iterable[tuple[str, int]]:
        """Returns (signal_name, list of sampled values) pairs."""
        for signal in self.group:
            yield signal, self[signal]

    def keys(self):
        """Return signal names in the group."""
        return self.group.keys()

    def __getitem__(self, key: str) -> int:
        """For the given signal name in the group, returns a list of sampled values."""
        if key not in self.group:
            raise ValueError(f"Signal '{key}' does not exist in group.")

        mask = self.group[key].mask
        shift = self.group[key].shift
        return (self.raw_data & mask) >> shift


@dataclass
class DebugBusSignalStoreInitialization:
    group_map: dict[str, tuple[int, int]]  # key: group_name, value: (daisy_sel, sig_sel)
    signals: dict[str, DebugBusSignalDescription]  # key: signal_name, value: signal description
    signal_groups: dict[
        str, dict[str, ShiftMask]
    ]  # key: group_name, value: signal_in_group on shift and mask in group mapping
    combined_signals: dict[str, list[str]]  # key: base signal name, value: list of combined signal parts


class DebugBusSignalStore:
    def __init__(
        self,
        initialization: DebugBusSignalStoreInitialization,
        noc_block: NocBlock,
        neo_id: int | None = None,
    ):
        self.group_map: dict[str, tuple[int, int]] = initialization.group_map
        self.signals: dict[str, DebugBusSignalDescription] = initialization.signals
        self.signal_groups: dict[str, dict[str, ShiftMask]] = initialization.signal_groups
        self.combined_signals: dict[str, list[str]] = initialization.combined_signals
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

    @staticmethod
    def get_base_signal_name(signal_name: str) -> str:
        """Extract base signal name from combined signal names like 'signal/suffix'."""
        return signal_name.split("/")[0] if "/" in signal_name else signal_name

    def get_signal_part_names(self, base_name: str) -> list[str]:
        """Get all part names for a combined signal based on its base name. Does not guarantee order."""
        if not self.is_combined_signal(base_name):
            return [base_name]

        return self.combined_signals[base_name]

    @staticmethod
    def is_signal_part(signal_name: str) -> bool:
        """Check if signal name indicates a combined signal part (ends with '/suffix')."""
        return "/" in signal_name

    def is_combined_signal(self, signal_name: str) -> bool:
        """Check if signal name is a base name for a combined signal (has /suffix variants)."""
        return signal_name in self.combined_signals

    def get_signal_names_in_group(self, group_name: str) -> Iterable[str]:
        """Get all signal names in the specified group."""
        if group_name not in self.signal_groups:
            raise ValueError(f"Unknown group name '{group_name}'.")

        return self.signal_groups[group_name].keys()

    @cached_property
    def signal_names(self) -> set[str]:
        """Get all signal names."""
        return set(self.signals.keys())

    @cached_property
    def group_names(self) -> set[str]:
        """Get all group names."""
        return set(self.group_map.keys())

    def get_signal_description(self, signal_name: str) -> DebugBusSignalDescription:
        """Returns the DebugBusSignalDescription for the given signal name."""
        if signal_name in self.signals:
            return self.signals[signal_name]
        elif self.neo_id is None:
            raise ValueError(
                f"Unknown signal name '{signal_name}' on {self.location.to_user_str()} for device {self.device._id}."
            )
        else:
            raise ValueError(
                f"Unknown signal name '{signal_name}' on {self.location.to_user_str()} [NEO {self.neo_id}] for device {self.device._id}."
            )

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
            raise ValueError(f"samples count must be at least 1, but got {samples}")

        if l1_address % 16 != 0:
            raise ValueError(f"L1 address must be 16-byte aligned, got 0x{l1_address:x}")

        # check that all samples fit within low 1MiB L1 memory range
        end_address = l1_address + (samples * self.L1_SAMPLE_SIZE_BYTES) - 1
        if end_address >= self.L1_LOW_MEMORY_SIZE:
            raise ValueError(f"L1 sampling range 0x{l1_address:x}-0x{end_address:x} exceeds 1 MiB limit")

        if samples > 1 and not (2 <= sampling_interval <= 256):
            raise ValueError(
                f"When sampling groups, sampling_interval must be between 2 and 256, but got {sampling_interval}"
            )

    def _read_signal_data(self, signal_desc: DebugBusSignalDescription) -> int:
        """Reads the 32 data register value from the debug bus using debug hardware"""
        # Configure debug bus to read the signal
        en = 1
        config = (en << 29) | (signal_desc.rd_sel << 25) | (signal_desc.daisy_sel << 16) | (signal_desc.sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )
        # Read the data
        return read_word_from_device(self.location, self._data_register_address, self.device._id, self.device._context)

    def read_signal(
        self,
        signal: DebugBusSignalDescription | str,
    ) -> int:
        """Reads a debug signal from the Tensix debug daisychain.

        **Direct Register Read:** Reads a 32-bit signal value directly
        from the debug register. It is possible to read all signals listed
        in the debug_bus_signal_map. For complex signals, only their parts,
        marked with the suffix /suffix, can be read atomically.

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

        # Read 32-bit data
        data = self._read_signal_data(signal_desc)

        # Apply mask
        value = data & signal_desc.mask

        # remove trailing zeros from mask
        return value >> ((signal_desc.mask & -signal_desc.mask).bit_length() - 1)

    def _read_signal_group_samples(
        self,
        signal_group: str,
        l1_address: int,
        samples: int = 1,
        sampling_interval: int = 2,
    ) -> list[SignalGroupSample]:
        """Internal method to read one or more samples from a signal group."""
        if self.device.is_quasar():
            raise NotImplementedError("Groups are only supported on Wormhole and Blackhole devices.")

        # Validate L1 address alignment and memory range
        self._validate_l1_parameters(l1_address, samples, sampling_interval)

        # Configure debug bus and setup L1 registers for sampling.
        reg2_addr, reg2_struct = self._setup_l1_sampling_configuration(
            signal_group, l1_address, samples, sampling_interval
        )

        # Execute L1 sampling and wait for completion
        self._execute_l1_sampling(reg2_addr, reg2_struct, l1_address, samples)
        return self._process_l1_samples(l1_address, signal_group, samples)

    def _setup_l1_sampling_configuration(
        self, signal_group: str, l1_address: int, samples: int = 1, sampling_interval: int = 2
    ) -> tuple[int, L1MemReg2]:
        """
        Configure debug bus and setup L1 memory registers for sampling
        Relevant documentation for wormhole although it also works on blackhole and quasar in similar or the same way:
        - https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/DebugDaisychain.md
        """
        # get daisy and sig selection for group
        daisy_sel, sig_sel = self.group_map[signal_group]

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

        # set configuration
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

    def _execute_l1_sampling(self, reg2_addr: int, reg2_struct: L1MemReg2, l1_address: int, samples: int = 1) -> None:
        """
        Execute L1 sampling process and wait for completion
        Relevant documentation for wormhole although it also works on blackhole and quasar in similar or the same way:
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

        # wait for the last memory location to be written to - using sentinel value as indicator
        while read_word_from_device(self.location, wait_addr, self.device._id, self.device._context) == SENTINEL_VALUE:
            sleep(WAIT_SLEEP_SECONDS)

    def _process_l1_samples(self, l1_address: int, group_name: str, samples: int = 1) -> list[SignalGroupSample]:
        """Process L1 samples and extract signal data based on signal configuration"""

        def read_sample(addr: int) -> int:
            """Read 4x32-bit words and combine them into a single 128-bit integer"""
            words = read_words_from_device(
                self.location, addr, self.device._id, self.WORDS_PER_SAMPLE, self.device._context
            )
            return sum((words[i] << (WORD_SIZE_BITS * i)) for i in range(self.WORDS_PER_SAMPLE))

        # Read samples from L1 memory
        sample_values = [read_sample(l1_address + (i * self.L1_SAMPLE_SIZE_BYTES)) for i in range(samples)]

        return [SignalGroupSample(sample, self.signal_groups[group_name]) for sample in sample_values]

    def sample_signal_group(
        self, signal_group: str, l1_address: int, samples: int = 1, sampling_interval: int = 2
    ) -> list[SignalGroupSample]:
        """Reads a debug signal group from the Tensix debug daisychain.

        **L1 Sampling:** Captures one or more 128-bit signal samples into L1
        memory and reads the result. Combined signals can be read fully, atomically,
        by specifying only the signal name without the /suffix.

        Parameters
        ----------
        signal_group : str
            The signal group to read. It is signal group name from `group_map`.
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
         list[SignalGroupSample]
            The object of SignalGroupSample which behaves like a dictionary: key is signal name, and
            value is sampled value for given signal name.
        """
        return self._read_signal_group_samples(signal_group, l1_address, samples, sampling_interval)

    def read_signal_group(
        self,
        signal_group: str,
        l1_address: int,
    ) -> SignalGroupSample:
        """Reads a debug signal group from the Tensix debug daisychain.

        **L1 Sampling:** Captures one 128-bit signal sample into L1
        memory and reads the result. Combined signals can be read fully, atomically,
        by specifying only the signal name without the part suffix.

        Parameters
        ----------
        signal_group : str
            The signal group to read. It is signal group name from `group_map`.
        l1_address : int
            Byte-address in L1 memory for the first 128-bit word. Must be 16-byte aligned.
            Must be within low L1 memory range (0x0 - 0xFFFFF, first 1 MiB). All samples must fit within this range.

        Returns
        -------
        SignalGroupSample
            The object of SignalGroupSample which behaves like a dictionary: key is signal name, and
            value is sampled value for given signal name.
        """
        return self._read_signal_group_samples(signal_group, l1_address, samples=1)[0]

    def read_signal_group_unsafe(self, signal_group: str) -> SignalGroupSample:
        daisy_sel, sig_sel = self.group_map[signal_group]
        data: int = 0  # 128-bit data
        # Read all 4 32-bit words (1 per read select)
        for rd_sel in range(4):
            signal_desc = DebugBusSignalDescription(rd_sel=rd_sel, daisy_sel=daisy_sel, sig_sel=sig_sel)
            data |= self._read_signal_data(signal_desc) << (WORD_SIZE_BITS * signal_desc.rd_sel)
        return SignalGroupSample(data, self.signal_groups[signal_group])

    @staticmethod
    def create_initialization(
        group_map: dict[str, tuple[int, int]],
        signals: dict[str, DebugBusSignalDescription],
    ) -> DebugBusSignalStoreInitialization:
        """
        This method creates an initialization object for debug bus signal store. Idea behind it is to create one initialization
        object per noc block type and then using that object create many debug bus signal stores that are tied to noc block. This
        way we save initialization time as creating store from initialization object is fast. It groups signals into signal groups
        based on the provided group map, calculating masks and shifts for each signal within the group.
        """
        # Build signal groups based on group map
        # dictionary where key is group name and value is dictionary of signals in that group
        signal_groups: dict[str, dict[str, ShiftMask]] = {}

        # dictionary where key is base signal name and value is list of combined signal parts
        combined_signals: dict[str, list[str]] = {}

        for group_key, (daisy_sel, sig_sel) in group_map.items():
            # group dictionary where key is signal name and value is ShiftMask for that signal
            signal_group: dict[str, ShiftMask] = {}
            for signal_name, signal_desc in signals.items():
                if signal_desc.daisy_sel == daisy_sel and signal_desc.sig_sel == sig_sel:
                    base_name = DebugBusSignalStore.get_base_signal_name(signal_name)
                    mask = signal_group[base_name].mask if base_name in signal_group else 0
                    mask |= signal_desc.mask << (WORD_SIZE_BITS * signal_desc.rd_sel)

                    # Compute mask and shift for the signal within the 128-bit sample.
                    signal_group[base_name] = ShiftMask(shift=(mask & -mask).bit_length() - 1, mask=mask)

                    # Build combined_signals dictionary
                    if DebugBusSignalStore.is_signal_part(signal_name):
                        base_name = DebugBusSignalStore.get_base_signal_name(signal_name)
                        if base_name not in combined_signals:
                            combined_signals[base_name] = []
                        combined_signals[base_name].append(signal_name)

            signal_groups[group_key] = signal_group

        return DebugBusSignalStoreInitialization(
            group_map=group_map,
            signals=signals,
            signal_groups=signal_groups,
            combined_signals=combined_signals,
        )
