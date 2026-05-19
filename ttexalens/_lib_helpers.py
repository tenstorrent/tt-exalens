# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import wraps
import inspect
from typing import TypeVar, Callable, Any, cast

from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.util import TTException, Verbosity, TRACE

# Parameter name to formatter function mapping for trace_api decorator
_TRACE_FORMATTERS = {
    "addr": hex,
}

F = TypeVar("F", bound=Callable[..., Any])


def trace_api(func: F) -> F:
    """Decorator to log API calls when verbosity is set to TRACE."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if Verbosity.supports(Verbosity.TRACE):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            formatted_args = []
            for k, v in bound_args.arguments.items():
                formatter = _TRACE_FORMATTERS.get(k, repr)
                formatted_args.append(f"{k}={formatter(v)}")
            TRACE(f"[API] {func.__name__}({', '.join(formatted_args)})")
        return func(*args, **kwargs)

    return cast(F, wrapper)


def check_context(context: Context | None = None) -> Context:
    """Function to initialize context if not provided. By default, it starts a local
    TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONTEXT variable so
    that the context can be reused in calls to other functions.
    """
    if context is not None:
        return context

    import ttexalens.tt_exalens_init as init

    if not init.GLOBAL_CONTEXT:
        init.GLOBAL_CONTEXT = init_ttexalens()
    return init.GLOBAL_CONTEXT


def check_noc_id(noc_id: int | None, context: Context) -> int:
    if noc_id is None:
        return 1 if context.use_noc1 else 0
    assert noc_id in (0, 1), f"Invalid NOC ID {noc_id}. Expected 0 or 1."
    return noc_id


def check_4B_mode(use_4B_mode: bool | None, context: Context) -> bool:
    if use_4B_mode is None:
        return context.use_4B_mode
    return use_4B_mode


def validate_addr(addr: int) -> None:
    if addr < 0:
        raise TTException("addr must be greater than or equal to 0.")


def validate_device_id(device_id: int, context: Context) -> Device:
    return context.find_device_by_id(device_id)


def convert_coordinate(
    location: str | OnChipCoordinate, device_id: int = 0, context: Context | None = None
) -> OnChipCoordinate:
    """
    Converts a string location to an OnChipCoordinate object.
    If location is already OnChipCoordinate, it is returned as-is.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        device_id (int, default 0): ID number of device to convert to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
        OnChipCoordinate: Converted coordinate.
    """
    if not isinstance(location, OnChipCoordinate):
        context = check_context(context)
        device = validate_device_id(device_id, context)
        return OnChipCoordinate.create(location, device)
    return location
