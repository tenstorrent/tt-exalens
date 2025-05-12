# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
from typing import Union

from ttexalens import tt_exalens_ifc
from ttexalens import tt_exalens_ifc_cache
from ttexalens import util as util

from ttexalens.context import Context, LimitedContext

"""
GLOBAL_CONTEXT is a convenience variable to store fallback TTExaLens context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that TTExaLens context is
a singleton, as it can be explicitly provided to library functions.
"""
GLOBAL_CONTEXT: Context = None


def init_ttexalens(
    wanted_devices: list = None,
    cache_path: str = None,
    init_jtag: bool = False,
    use_noc1: bool = False,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is local, through pybind.

    Args:
            wanted_devices (list, optional): List of device IDs we want to connect to. If None, connect to all available devices.
            caching_path (str, optional): Path to the cache file to write. If None, caching is disabled.

    Returns:
            Context: TTExaLens context object.
    """

    lens_ifc = tt_exalens_ifc.init_pybind(wanted_devices, init_jtag, use_noc1)
    if cache_path:
        lens_ifc = tt_exalens_ifc_cache.init_cache_writer(lens_ifc, cache_path)

    return load_context(lens_ifc, use_noc1)


def init_ttexalens_remote(
    ip_address: str = "localhost",
    port: int = 5555,
    cache_path: str = None,
) -> Context:
    """Initializes TTExaLens internals by creating the device interface and TTExaLens context.
    Interfacing device is done remotely through TTExaLens client.

    Args:
            ip_address (str): IP address of the TTExaLens server. Default is 'localhost'.
            port (int): Port number of the TTExaLens server interface. Default is 5555.
            cache_path (str, optional): Path to the cache file to write. If None, caching is disabled.

    Returns:
            Context: TTExaLens context object.
    """

    lens_ifc = tt_exalens_ifc.connect_to_server(ip_address, port)
    if cache_path:
        lens_ifc = tt_exalens_ifc_cache.init_cache_writer(lens_ifc, cache_path)

    return load_context(lens_ifc)


def init_ttexalens_cached(
    cache_path: str,
):
    """Initializes TTExaLens internals by reading cached session data. There is no connection to the device.
    Only cached commands are available.

    Args:
            cache_path (str): Path to the cache file.

    Returns:
            Context: TTExaLens context object.
    """
    if not os.path.exists(cache_path) or not os.path.isfile(cache_path):
        raise util.TTFatalException(f"Error: Cache file at {cache_path} does not exist.")

    lens_ifc = tt_exalens_ifc_cache.init_cache_reader(cache_path)

    return load_context(lens_ifc)


def get_cluster_desc_yaml(lens_ifc: tt_exalens_ifc.TTExaLensCommunicator) -> util.YamlFile:
    """Get the runtime data and cluster description yamls through the TTExaLens interface."""

    try:
        cluster_desc_path = lens_ifc.get_cluster_description()
        cluster_desc_yaml = util.YamlFile(lens_ifc, cluster_desc_path)
    except:
        raise util.TTFatalException("TTExaLens does not support cluster description. Cannot connect to device.")

    return cluster_desc_yaml


def load_context(server_ifc: tt_exalens_ifc.TTExaLensCommunicator, use_noc1: bool = False) -> Context:
    """Load the TTExaLens context object with specified parameters."""
    context = LimitedContext(server_ifc, get_cluster_desc_yaml(server_ifc), use_noc1)

    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = context

    return context


def set_active_context(context: Context) -> None:
    """
    Set the active TTExaLens context object.

    Args:
            context (Context): TTExaLens context object.

    Notes:
            - Every new context initialization will overwrite the currently active context.
    """
    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = context


def locate_most_recent_build_output_dir() -> Union[str, None]:
    """Try to find a default output directory."""
    most_recent_modification_time = None
    try:
        for tt_build_subfile in os.listdir("tt_build"):
            subdir = f"tt_build/{tt_build_subfile}"
            if os.path.isdir(subdir):
                if most_recent_modification_time is None or os.path.getmtime(subdir) > most_recent_modification_time:
                    most_recent_modification_time = os.path.getmtime(subdir)
                    most_recent_subdir = subdir
        return most_recent_subdir
    except:
        return None
