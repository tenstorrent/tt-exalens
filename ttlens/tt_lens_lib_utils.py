# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# Core utility functions used by tt_lens_lib and other modules
from ttlens import tt_lens_init
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from typing import Union, List

def check_context(context: Context = None) -> Context:
    """Function to initialize context if not provided. By default, it starts a local
    TTLens session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
    that the context can be reused in calls to other functions.
    """
    if context is not None:
        return context

    if not tt_lens_init.GLOBAL_CONTEXT:
        tt_lens_init.GLOBAL_CONTEXT = tt_lens_init.init_ttlens()
    return tt_lens_init.GLOBAL_CONTEXT


def validate_addr(addr: int) -> None:
    if addr < 0:
        raise TTException("addr must be greater than or equal to 0.")


def validate_device_id(device_id: int, context: Context) -> None:
    if device_id not in context.device_ids:
        raise TTException(f"Invalid device_id {device_id}.")


def arc_read(context: Context, device_id: int, core_loc: tuple, reg_addr: int) -> int:
    """
    Reads a 32-bit value from an ARC address space.
    """
    if context.devices[device_id]._has_mmio:
        read_val = context.server_ifc.pci_read32_raw(device_id, reg_addr)
    else:
        read_val = context.server_ifc.pci_read32(device_id, *core_loc.to("virtual"), reg_addr)
    return read_val


def arc_write(context: Context, device_id: int, core_loc: tuple, reg_addr: int, value: int) -> None:
    """
    Writes a 32-bit value to an ARC address space.
    """
    if context.devices[device_id]._has_mmio:
        context.server_ifc.pci_write32_raw(device_id, reg_addr, value)
    else:
        context.server_ifc.pci_write32(device_id, *core_loc.to("virtual"), reg_addr, value)
        
def split_32bit_to_16bit(value: int) -> List[int]:
    """
    Splits a 32-bit integer into two 16-bit integers.

    Args:
        value: The 32-bit value to split.

    Returns: A list of two 16-bit values that represent the 32-bit value.
    """
    return [value & 0xffff, (value >> 16) & 0xffff]
