# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os

from ttexalens.umd_api import UmdApi, local_init
from ttexalens.server import FileAccessApi, connect_to_server
from ttexalens import util as util
from ttexalens.context import Context

"""
GLOBAL_CONTEXT is a convenience variable to store fallback TTExaLens context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that TTExaLens context is
a singleton, as it can be explicitly provided to library functions.
"""
GLOBAL_CONTEXT: Context | None = None


def init_ttexalens(
    init_jtag: bool = False,
    use_noc1: bool = False,
    use_4B_mode: bool = True,
    simulation_directory: str | None = None,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is local, through pybind.

    Args:
        init_jtag (bool): Whether to initialize JTAG interface. Default is False.
        use_noc1 (bool): Whether to initialize with NOC1 and use NOC1 for communication with the device. Default is False.
        use_4B_mode (bool): Whether to use 4B mode for communication with the device. Default is True.
        simulation_directory (str, optional): If specified, starts the simulator from the given build output directory.

    Returns:
        Context: TTExaLens context object.
    """

    umd_api = local_init(init_jtag, use_noc1, simulation_directory)

    return load_context(umd_api, FileAccessApi(), use_noc1, use_4B_mode)


def init_ttexalens_remote(
    ip_address: str = "localhost",
    port: int = 5555,
    use_4B_mode: bool = True,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is done remotely through TTExaLens client.

    Args:
            ip_address (str): IP address of the TTExaLens server. Default is 'localhost'.
            port (int): Port number of the TTExaLens server interface. Default is 5555.
            use_4B_mode (bool): Whether to use 4B mode for communication with the device. Default is True.

    Returns:
            Context: TTExaLens context object.
    """

    umd_api, file_api = connect_to_server(ip_address, port)

    return load_context(umd_api, file_api, use_4B_mode=use_4B_mode)


def get_cluster_desc_yaml(umd_api: UmdApi, file_api: FileAccessApi) -> util.YamlFile:
    """Get the runtime data and cluster description yamls through the TTExaLens interface."""

    try:
        cluster_desc_path = umd_api.get_cluster_description()
        cluster_desc_yaml = util.YamlFile(file_api, cluster_desc_path)
    except:
        raise util.TTFatalException("TTExaLens does not support cluster description. Cannot connect to device.")

    return cluster_desc_yaml


def load_context(umd_api: UmdApi, file_api: FileAccessApi, use_noc1: bool = False, use_4B_mode: bool = True) -> Context:
    """Load the TTExaLens context object with specified parameters."""
    context = Context(
        umd_api, file_api, get_cluster_desc_yaml(umd_api, file_api), use_noc1=use_noc1, use_4B_mode=use_4B_mode
    )

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
