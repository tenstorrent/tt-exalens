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
WAIT_SLEEP_MS = 0.001
SENTINEL_VALUE = 0xACAFACA

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
    sampling_interval: int = 0
    write_mode: int = 0

    def encode(self) -> int:
        val = 0
        val |= (self.write_trigger & 0x1) << 12
        val |= (self.sampling_interval & 0xFF) << 4
        val |= (self.write_mode & 0xF)
        return val

    @classmethod
    def decode(cls, raw: int) -> "L1MemReg2":
        return cls(
            write_trigger=(raw >> 12) & 0x1,
            sampling_interval=(raw >> 4) & 0xFF,
            write_mode=raw & 0xF,
        )



class DebugBusSignalStore:
    def __init__(self, signals: dict[str, DebugBusSignalDescription], group_signals: dict[str, list[str]], noc_block: NocBlock, neo_id: int | None = None):
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

    @cached_property
    def _control_register_address(self) -> int:
        address = self._register_store.get_register_noc_address("RISCV_DEBUG_REG_DBG_BUS_CNTL_REG")
        assert address is not None, "Control register address not found in register store."
        return address

    @cached_property
    def _data_register_address(self) -> int:
        address = self._register_store.get_register_noc_address("RISCV_DEBUG_REG_DBG_RD_DATA")
        assert address is not None, "Data register address not found in register store."
        return address
    
    @staticmethod
    def get_signal_groups(signal_map: dict, group_names: dict) -> dict:
        groups = {}
        for signal_name, signal_desc in signal_map.items():
            key = (signal_desc.daisy_sel, signal_desc.sig_sel)
            group_key = group_names[key]
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(signal_name)
        
        return groups

    def get_signal_names(self) -> Iterable[str]:
        return self.signals.keys()

    def _validate_signal_parameters(self, signal: DebugBusSignalDescription) -> None:
        """Validate signal parameters are within expected ranges"""
        if not (0 <= signal.rd_sel <= 3):
            raise ValueError(f"rd_sel must be between 0 and 3, got {signal.rd_sel}")
        
        if not (0 <= signal.daisy_sel <= 255):
            raise ValueError(f"daisy_sel must be between 0 and 255, got {signal.daisy_sel}")
        
        if not (0 <= signal.sig_sel <= 65535):
            raise ValueError(f"sig_sel must be between 0 and 65535, got {signal.sig_sel}")
        
        if not (0 <= signal.mask <= 0xFFFFFFFF):
            raise ValueError(f"mask must be a valid 32-bit integer, got {signal.mask}")

    def is_combined_signal(self, signal_name: str) -> bool:
        """Check if signal_name is a base name for a combined signal (has /0, /1, /2... variants)"""
        return f"{signal_name}/0" in self.signals

    def get_signal_description(self, signal_name: str) -> list[DebugBusSignalDescription]:
        # First check if exact signal exists
        if signal_name in self.signals:
            return [self.signals[signal_name]]
        
        # If not found, check if it's a base name for combined signal
        if self.is_combined_signal(signal_name):
            # For combined signals, return list of all signal parts (/0, /1, /2, ...)
            combined_signals = []
            counter = 0
            while True:
                part_signal_name = f"{signal_name}/{counter}"
                if part_signal_name in self.signals:
                    combined_signals.append(self.signals[part_signal_name])
                    counter += 1
                else:
                    break
            return combined_signals
        
        # Signal not found - raise error with appropriate context
        neo_context = f" [NEO {self.neo_id}]" if self.neo_id is not None else ""
        raise ValueError(
            f"Unknown signal name '{signal_name}' on {self.location.to_user_str()}{neo_context} for device {self.device._id}."
        )

    def read_signal(
        self,
        signal: DebugBusSignalDescription | str,
        use_l1_sampling: bool = False,
        l1_address: int = 0,
        samples: int = 1,
        sampling_interval: int = 2,
    ) -> int | list[int]:
        """Reads a debug signal from the Tensix debug daisychain.

        This function can operate in two modes:
        1.  **Direct Register Read (default):** Reads a 32-bit signal value directly 
            from the debug register. This is the default behavior when `use_l1_sampling=False`.
        2.  **L1 Sampling:** Captures one or more 128-bit signal samples into L1 
            memory and reads the result. Enabled by setting `use_l1_sampling=True`.

        Parameters
        ----------
        signal : DebugBusSignalDescription | str
            The signal to read. Can be a string (signal name) or a DebugBusSignalDescription object.
        use_l1_sampling : bool, default=False
            If True, enables L1 sampling mode. Otherwise, performs a direct register read.
        l1_address : int, default=0
            (L1 Sampling only) Byte-address in L1 memory for the first 128-bit word. Must be 16-byte aligned.
        samples : int, default=1
            (L1 Sampling only) Number of 128-bit samples to capture. If `samples > 1`, hardware performs repeated sampling.
        sampling_interval : int, default=0
            (L1 Sampling only) Interval (in cycles) between consecutive samples when `samples > 1`.
            Should be ≥ 2 due to a known hardware bug that may cause one extra sample if `sampling_period == 1`

        Returns
        -------
        int
            The sampled data. A 32-bit value in direct read mode, or a 128-bit value in L1 sampling mode.
            The value is masked with `signal.mask` if set.
        """
        if isinstance(signal, str):
            signal = self.get_signal_description(signal)
        else:
            # Validate signal parameters if passed as DebugBusSignalDescription
            self._validate_signal_parameters(signal)

        # Check if this is a combined signal and enforce L1 sampling
        if len(signal) > 1 and not use_l1_sampling:
            raise ValueError(
                f"Combined signal can only be read using L1 sampling. "
                f"Use --l1-sampling flag to read this signal."
            )

        if use_l1_sampling:
            return self._read_signal_from_l1(
                signal, l1_address, samples, sampling_interval
            )

        # Default behavior: read from 32bit debug register
        en = 1
        config = (en << 29) | (signal[0].rd_sel << 25) | (signal[0].daisy_sel << 16) | (signal[0].sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )

        data = read_word_from_device(self.location, self._data_register_address, self.device._id, self.device._context)

        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)

        return data if signal[0].mask is None else data & signal[0].mask

    def _read_signal_from_l1(
        self,
        signal: list[DebugBusSignalDescription],
        l1_address: int,
        samples: int,
        sampling_interval: int,
    ) -> int | list[int]:
        """Read signal(s) using L1 memory sampling method"""
        if samples < 1:
            raise ValueError(f"samples must be at least 1, but got {samples}")

        if samples > 1:
            if not (2 <= sampling_interval <= 256):
                raise ValueError(
                    f"When samples > 1, sampling_interval must be between 2 and 256, but got {sampling_interval}"
                )

        # Write the configuration - select 128 bit word
        en = 1
        config = (en << 29) | (signal[0].daisy_sel << 16) | (signal[0].sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )

        reg0_addr = self._register_store.get_register_noc_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG0")
        reg1_addr = self._register_store.get_register_noc_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG1")
        reg2_addr = self._register_store.get_register_noc_address("RISCV_DEBUG_REG_DBG_L1_MEM_REG2")

        reg2_struct = L1MemReg2(
            write_trigger=0, 
            sampling_interval=0, 
            write_mode=0
        )

        # prepare L1 writing
        reg2_struct.write_mode = 0xF
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        reg0_val = (l1_address >> 4) & 0xFFFFFFFF
        write_words_to_device(self.location, reg0_addr, reg0_val, self.device._id, self.device._context)

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

        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)

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
        while True:
            val = read_word_from_device(self.location, wait_addr, self.device._id, self.device._context)
            if val != SENTINEL_VALUE:
                break
            sleep(WAIT_SLEEP_MS)
        
        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)

        # Helper function to read and convert 128-bit data
        def read_128bit_sample(addr: int) -> int:
            """Read 4x32-bit words and combine them into a single 128-bit integer"""
            words = read_words_from_device(self.location, addr, self.device._id, WORDS_PER_SAMPLE, self.device._context)
            return sum((words[i] << (WORD_SIZE_BITS * i)) for i in range(WORDS_PER_SAMPLE))

        # Read all samples and extract the correct portion based on signal type
        sample_values = []
        for i in range(samples):
            sample_data = read_128bit_sample(l1_address + (i * L1_SAMPLE_SIZE_BYTES))
            
            if len(signal) > 1:
                # Combined signal - read each part and combine them
                combined_value = 0
                for j, signal_part in enumerate(signal):
                    extracted_value = (sample_data >> (WORD_SIZE_BITS * signal_part.rd_sel)) & 0xFFFFFFFF
                    masked_value = extracted_value & signal_part.mask
                    combined_value |= (masked_value << (WORD_SIZE_BITS * j))
                
                # Count trailing zeros in first signal's mask and shift combined value
                count = (signal[0].mask & -signal[0].mask).bit_length() - 1 
                combined_value = combined_value >> count
                sample_values.append(combined_value)
            else:
                # Single signal - extract 32-bit value using rd_sel
                extracted_value = (sample_data >> (WORD_SIZE_BITS * signal[0].rd_sel)) & 0xFFFFFFFF
                masked_value = extracted_value & signal[0].mask
                sample_values.append(masked_value)
        
        return sample_values[0] if samples == 1 else sample_values


