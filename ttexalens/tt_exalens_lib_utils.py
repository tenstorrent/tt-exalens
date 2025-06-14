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
