# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os

from ttexalens import tt_exalens_ifc
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

    lens_ifc = tt_exalens_ifc.local_init(init_jtag, use_noc1, simulation_directory)

    return load_context(lens_ifc, use_noc1, use_4B_mode)


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

    lens_ifc = tt_exalens_ifc.connect_to_server(ip_address, port)

    return load_context(lens_ifc, use_4B_mode=use_4B_mode)


def get_cluster_desc_yaml(lens_ifc: tt_exalens_ifc.TTExaLensUmdImplementation) -> util.YamlFile:
    """Get the runtime data and cluster description yamls through the TTExaLens interface."""

    try:
        cluster_desc_path = lens_ifc.get_cluster_description()
        cluster_desc_yaml = util.YamlFile(lens_ifc, cluster_desc_path)
    except:
        raise util.TTFatalException("TTExaLens does not support cluster description. Cannot connect to device.")

    return cluster_desc_yaml


def load_context(
    server_ifc: tt_exalens_ifc.TTExaLensUmdImplementation, use_noc1: bool = False, use_4B_mode: bool = True
) -> Context:
    """Load the TTExaLens context object with specified parameters."""
    context = Context(server_ifc, get_cluster_desc_yaml(server_ifc), use_noc1=use_noc1, use_4B_mode=use_4B_mode)

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


def locate_most_recent_build_output_dir() -> str | None:
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
