# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# Core utility functions used by tt_exalens_lib and other modules
from ttexalens import tt_exalens_init
from ttexalens.context import Context
from ttexalens.util import TTException


def check_context(context: Context = None) -> Context:
    """Function to initialize context if not provided. By default, it starts a local
    TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
    that the context can be reused in calls to other functions.
    """
    if context is not None:
        return context

    if not tt_exalens_init.GLOBAL_CONTEXT:
        tt_exalens_init.GLOBAL_CONTEXT = tt_exalens_init.init_ttexalens()
    return tt_exalens_init.GLOBAL_CONTEXT


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
    noc_id = 1 if context.use_noc1 else 0
    if context.devices[device_id]._has_mmio:
        read_val = context.server_ifc.pci_read32_raw(device_id, reg_addr)
    else:
        read_val = context.server_ifc.pci_read32(noc_id, device_id, *context.convert_loc_to_umd(core_loc), reg_addr)
    return read_val


def arc_write(context: Context, device_id: int, core_loc: tuple, reg_addr: int, value: int) -> None:
    """
    Writes a 32-bit value to an ARC address space.
    """
    noc_id = 1 if context.use_noc1 else 0
    if context.devices[device_id]._has_mmio:
        context.server_ifc.pci_write32_raw(device_id, reg_addr, value)
    else:
        context.server_ifc.pci_write32(noc_id, device_id, *context.convert_loc_to_umd(core_loc), reg_addr, value)
