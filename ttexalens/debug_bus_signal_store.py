# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, Iterable, TYPE_CHECKING

from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.device import Device


@dataclass
class DebugBusSignalDescription:
    rd_sel: int = 0
    daisy_sel: int = 0
    sig_sel: int = 0
    mask: int = 0xFFFFFFFF


class DebugBusSignalStore:
    def __init__(
        self, signals: Dict[str, DebugBusSignalDescription], location: OnChipCoordinate, neo_id: int | None = None
    ):
        self.signals = signals
        self.location = location
        self.neo_id = neo_id

    @property
    def device(self) -> Device:
        return self.location._device

    @cached_property
    def _control_register_address(self) -> int:
        # TODO: This should be read from register store (once we have it). Register store should be argument to the constructor.
        return self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_BUS_CNTL_REG")

    @cached_property
    def _data_register_address(self) -> int:
        # TODO: This should be read from register store (once we have it). Register store should be argument to the constructor.
        return self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_RD_DATA")

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

    def read_signal(self, signal: DebugBusSignalDescription | str) -> int:
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
