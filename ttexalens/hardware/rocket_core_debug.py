# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator

from ttexalens.hardware.risc_debug import RiscDebug


class RocketCoreDebug(RiscDebug):
    def is_in_reset(self) -> bool:
        raise NotImplementedError("is_in_reset must be implemented by subclasses of RocketCoreDebug")

    def set_reset_signal(self, value: bool) -> None:
        raise NotImplementedError("set_reset_signal must be implemented by subclasses of RocketCoreDebug")

    @contextmanager
    def ensure_debug_module_out_of_reset(self) -> Generator[None, Any, None]:
        raise NotImplementedError(
            "ensure_debug_module_out_of_reset must be implemented by subclasses of RocketCoreDebug"
        )

    def is_halted(self) -> bool:
        raise NotImplementedError("is_halted must be implemented by subclasses of RocketCoreDebug")

    def halt(self) -> None:
        raise NotImplementedError("halt must be implemented by subclasses of RocketCoreDebug")

    def cont(self) -> None:
        raise NotImplementedError("cont must be implemented by subclasses of RocketCoreDebug")

    @contextmanager
    def ensure_halted(self) -> Generator[None, Any, None]:
        raise NotImplementedError("ensure_halted must be implemented by subclasses of RocketCoreDebug")

    def get_pc(self) -> int:
        raise NotImplementedError("get_pc must be implemented by subclasses of RocketCoreDebug")

    def set_code_start_address(self, address: int | None) -> None:
        raise NotImplementedError("set_code_start_address must be implemented by subclasses of RocketCoreDebug")
