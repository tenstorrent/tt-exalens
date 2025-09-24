# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable, TYPE_CHECKING

from ttexalens.hardware.noc_block import NocBlock
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device

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
    def __init__(self, signals: dict[str, DebugBusSignalDescription], noc_block: NocBlock, neo_id: int | None = None):
        self.signals = signals
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

    def get_signal_names(self) -> Iterable[str]:
        return self.signals.keys()

    def get_signal_description(self, signal_name: str) -> DebugBusSignalDescription:
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

    def read_signal_32(self, signal: DebugBusSignalDescription | str) -> int:
        if isinstance(signal, str):
            signal = self.get_signal_description(signal)
        else:
            if not (0 <= signal.rd_sel <= 3):  # Example range, update if needed
                raise ValueError(f"rd_sel must be between 0 and 3, got {signal.rd_sel}")

            if not (0 <= signal.daisy_sel <= 255):  # Example range, update if needed
                raise ValueError(f"daisy_sel must be between 0 and 255, got {signal.daisy_sel}")

            if not (0 <= signal.sig_sel <= 65535):  # Example range, update if needed
                raise ValueError(f"sig_sel must be between 0 and 65535, got {signal.sig_sel}")

            if not (0 <= signal.mask <= 0xFFFFFFFF):  # Mask should be a valid 32-bit value
                raise ValueError(f"mask must be a valid 32-bit integer, got {signal.mask}")

        # Write the configuration
        en = 1
        config = (en << 29) | (signal.rd_sel << 25) | (signal.daisy_sel << 16) | (signal.sig_sel << 0)
        write_words_to_device(
            self.location, self._control_register_address, config, self.device._id, self.device._context
        )

        # Read the data
        data = read_word_from_device(self.location, self._data_register_address, self.device._id, self.device._context)

        # Disable the signal
        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)

        return data if signal.mask is None else data & signal.mask



    # TODO: Add parameter check
    def read_signal_128(self, signal: DebugBusSignalDescription | str, l1_address: int, samples: int = 1, sampling_interval: int = 1, write_mode: int = 1) -> int:
        if isinstance(signal, str):
            signal = self.get_signal_description(signal)

        if not (0 <= signal.rd_sel <= 3):  # Example range, update if needed
            raise ValueError(f"rd_sel must be between 0 and 3, got {signal.rd_sel}")

        if not (0 <= signal.daisy_sel <= 255):  # Example range, update if needed
            raise ValueError(f"daisy_sel must be between 0 and 255, got {signal.daisy_sel}")

        if not (0 <= signal.sig_sel <= 65535):  # Example range, update if needed
            raise ValueError(f"sig_sel must be between 0 and 65535, got {signal.sig_sel}")

        if not (0 <= signal.mask <= 0xFFFFFFFF):  # Mask should be a valid 32-bit value
            raise ValueError(f"mask must be a valid 32-bit integer, got {signal.mask}")

        # Write the configuration - select 128 bit word
        en = 1
        config = (en << 29) | (signal.daisy_sel << 16) | (signal.sig_sel << 0)
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
        # prepare
        reg2_struct.write_mode = 0xF
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        reg0_val = (l1_address >> 4) & 0xFFFFFFFF
        write_words_to_device(self.location, reg0_addr, reg0_val, self.device._id, self.device._context)

        if sampling_interval:
            reg1_val = ((l1_address >> 4) + samples) & 0xFFFFFFFF
            write_words_to_device(self.location, reg1_addr, reg1_val, self.device._id, self.device._context)
            reg2_struct.write_mode = 4
            reg2_struct.sampling_interval = sampling_interval - 1  # hardware bug, when N==1, hardware might take one more sample than requested
            reg2_struct.write_trigger = 1
        else:
            reg2_struct.write_mode = write_mode
            write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)

        # instruct to write
        reg2_struct.write_trigger = 1
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        reg2_struct.write_trigger = 0
        write_words_to_device(self.location, reg2_addr, reg2_struct.encode(), self.device._id, self.device._context)
        
        # location of last 128-bit word in L1
        expected_last = (l1_address >> 4) + (samples - 1 if write_mode == 1 else 0)


        # Disable the signal - da li ce prekinutio samplovanje!?
        write_words_to_device(self.location, self._control_register_address, 0, self.device._id, self.device._context)
        # read from L1 
        data = 0
        return data if signal.mask is None else data & signal.mask

# read 128 bits
# write config

# write in L1:
# prepare:
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 (reserved(19), writeTrigger(1), SamplingInenterval(8), WriteMode(4))
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 = 0xF    (WriteMode = 0xF and rest = 0)
# ***RISCV_DEBUG_REG_DBG_L1_MEM_REG0 = (x >> 4)    (x - byte-address in L1)
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 = 0x0 ili 0x1   (writeMode = 1 ili 0)  

# instruct to write:
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 = (set writeTrigger to 1 and rest same as before) - can wait up to 200 cycles if L1 is busy.
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 = (set writeTrigger to 0 and rest same as before) 
# if writeMode = 0: 
#     write on same address in next iteration
# if writeMode = 1:
#     increment address in next iteration - 16 bytes after

# samples:
# after *** instruction
# RISCV_DEBUG_REG_DBG_L1_MEM_REG1 = (x >> 4) + c  (c - number of samples)
# RISCV_DEBUG_REG_DBG_L1_MEM_REG2 = (WriteMode == 4, SamplingInterval = N-1 - to get a 
# sample every N cycles - not precise (if misses, it will try again after N cycles), WriteTrigger == true) - hardware bug, when N==1, 
# hardware might take one more sample than requested




