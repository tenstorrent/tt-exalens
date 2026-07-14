# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import atexit

from ttexalens.umd_api import UmdApi, local_init
from ttexalens.server import FileAccessApi, connect_to_server
from ttexalens import util as util
from ttexalens.context import Context, NocId, to_noc_id

"""
GLOBAL_CONTEXT is a convenience variable to store fallback TTExaLens context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that TTExaLens context is
a singleton, as it can be explicitly provided to library functions.
"""
GLOBAL_CONTEXT: Context | None = None


def init_ttexalens(
    init_jtag: bool = False,
    noc_id: NocId = NocId.NOC1,
    simulation_directory: str | None = None,
    noc_failover: bool = True,
    safe_mode: bool = True,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is local, through pybind.

    Args:
        init_jtag (bool): Whether to initialize JTAG interface. Default is False.
        noc_id (NocId): NOC used for all communication with the device, including topology discovery
            (NocId.NOC0, NocId.NOC1, or NocId.SYSTEM_NOC). Default is NocId.NOC1 except for Quasar which uses NocId.NOC0 as default.
        simulation_directory (str, optional): If specified, starts the simulator from the given build output directory.
        safe_mode (bool): Whether to enable safe mode for memory access. Default is True.

    Returns:
        Context: TTExaLens context object.
    """
    noc_id = to_noc_id(noc_id)

    # Since Quasar is only available through simulation as workaround if we are using simulator we switch to NOC0
    if simulation_directory is not None and noc_id == NocId.NOC1:
        noc_id = NocId.NOC0

    umd_api = local_init(init_jtag, noc_id, simulation_directory)

    return load_context(umd_api, FileAccessApi(), noc_id, noc_failover=noc_failover, safe_mode=safe_mode)


def init_ttexalens_remote(
    ip_address: str = "localhost",
    port: int = 5555,
    noc_failover: bool = True,
    safe_mode: bool = True,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is done remotely through TTExaLens client.

    Args:
            ip_address (str): IP address of the TTExaLens server. Default is 'localhost'.
            port (int): Port number of the TTExaLens server interface. Default is 5555.
            safe_mode (bool): Whether to enable safe mode for memory access. Default is True.

    Returns:
            Context: TTExaLens context object.
    """

    umd_api, file_api = connect_to_server(ip_address, port)

    return load_context(umd_api, file_api, noc_failover=noc_failover, safe_mode=safe_mode)


def load_context(
    umd_api: UmdApi,
    file_api: FileAccessApi,
    noc_id: NocId | None = None,
    noc_failover: bool = True,
    safe_mode: bool = True,
) -> Context:
    """Load the TTExaLens context object with specified parameters."""
    if noc_id is None:
        noc_id = umd_api.initialization_noc_id

    context = Context(umd_api, file_api, noc_id=noc_id, noc_failover=noc_failover, safe_mode=safe_mode)

    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = context

    return context


def set_active_context(context: Context | None) -> None:
    """
    Set the active TTExaLens context object.

    Args:
            context (Context): TTExaLens context object.

    Notes:
            - Every new context initialization will overwrite the currently active context.
    """
    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = context


def cleanup_global_context():
    """
    Clears the global context reference to allow C++ destructors
    to run before the nanobind runtime shuts down.
    """
    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = None


# Register the cleanup to run automatically on script exit
atexit.register(cleanup_global_context)
