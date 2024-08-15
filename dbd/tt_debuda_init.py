# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
from typing import Union

from dbd import tt_debuda_ifc
from dbd import tt_debuda_ifc_cache
from dbd import tt_util as util

from dbd.tt_debuda_context import Context, BudaContext, LimitedContext

"""
GLOBAL_CONTEXT is a convenience variable to store fallback debuda context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that debuda context is
a singleton, as it can be explicitly provided to library functions.
"""
GLOBAL_CONTEXT: Context = None


def init_debuda(
		output_dir_path: str = None,
		netlist_path: str = None,
		wanted_devices: list = None,
		cache_path: str = None,
) -> Context:
	""" Initializes debuda internals by creating the device interface and debuda context.
	Interfacing device is local, through pybind.

	Args:
		output_dir_path (str, optional): Path to the debuda run output directory. If None, debuda will be initialized in limited mode.
		netlist_path (str, optional): Path to the netlist file.
		wanted_devices (list, optional): List of device IDs we want to connect to. If None, connect to all available devices.
		caching_path (str, optional): Path to the cache file to write. If None, caching is disabled.
		
	Returns:
		Context: Debuda context object.
	"""
	runtime_data_yaml_filename = None
	if output_dir_path:
		runtime_data_yaml_filename = find_runtime_data_yaml_filename(output_dir_path)
	debuda_ifc = tt_debuda_ifc.init_pybind(str(runtime_data_yaml_filename or ""), output_dir_path, wanted_devices)
	if cache_path:
		debuda_ifc = tt_debuda_ifc_cache.init_cache_writer(cache_path)
	
	runtime_data_yaml, cluster_desc_yaml = get_yamls(debuda_ifc)

	return load_context(debuda_ifc, netlist_path, runtime_data_yaml, cluster_desc_yaml)


def init_debuda_remote(
		ip_address: str = 'localhost',
		port: int = 5555,
		cache_path: str = None,
) -> Context:
	""" Initializes debuda internals by creating the device interface and debuda context.
	Interfacing device is done remotely through debuda client.

	Args:
		ip_address (str): IP address of the debuda server. Default is 'localhost'.
		port (int): Port number of the debuda server interface. Default is 5555.
		cache_path (str, optional): Path to the cache file to write. If None, caching is disabled.
		
	Returns:
		Context: Debuda context object.
	"""

	debuda_ifc = tt_debuda_ifc.connect_to_server(ip_address, port)
	if cache_path:
		debuda_ifc = tt_debuda_ifc_cache.init_cache_writer(cache_path)

	runtime_data_yaml, cluster_desc_yaml = get_yamls(debuda_ifc)

	return load_context(debuda_ifc, None, runtime_data_yaml, cluster_desc_yaml)


def init_debuda_cached(
		cache_path: str,
		netlist_path: str = None,
):
	"""Initializes debuda internals by reading cached session data. There is no connection to the device.
	Only cached commands are available.

	Args:
		cache_path (str): Path to the cache file.
		netlist_path (str, optional): Path to the netlist file.

	Returns:
		Context: Debuda context object.
	"""
	if not os.path.exists(cache_path) or not os.path.isfile(cache_path):
		raise util.TTFatalException(f"Error: Cache file at {cache_path} does not exist.")
	
	debuda_ifc = tt_debuda_ifc_cache.init_cache_reader(cache_path)
	runtime_data_yaml, cluster_desc_yaml = get_yamls(debuda_ifc)

	return load_context(debuda_ifc, netlist_path, runtime_data_yaml, cluster_desc_yaml)


def get_yamls(debuda_ifc: tt_debuda_ifc.DbdCommunicator) -> "tuple[util.YamlFile, util.YamlFile]":
	""" Get the runtime data and cluster description yamls through the debuda interface.
	"""
	try:
		runtime_data = debuda_ifc.get_runtime_data()
		runtime_data_yaml = util.YamlFile(debuda_ifc, 'runtime_yaml', content=runtime_data)
	except:
		# It is OK to continue with limited functionality
		runtime_data_yaml = None

	try:
		cluster_desc_path = debuda_ifc.get_cluster_description()
		cluster_desc_yaml = util.YamlFile(debuda_ifc, cluster_desc_path)
	except:
		raise util.TTFatalException("Debuda does not support cluster description. Cannot connect to device.")

	return runtime_data_yaml, cluster_desc_yaml


def load_context(
		server_ifc: tt_debuda_ifc.DbdCommunicator, 
		netlist_filepath: str, 
		runtime_data_yaml: util.YamlFile, 
		cluster_desc_yaml: util.YamlFile
) -> Context:
    """ Load the debuda context object with specified parameters. """
    run_dirpath = server_ifc.get_run_dirpath()
    if run_dirpath is None or runtime_data_yaml is None:
        context = LimitedContext(server_ifc, cluster_desc_yaml)
    else:
        context = BudaContext(server_ifc, netlist_filepath, run_dirpath, runtime_data_yaml, cluster_desc_yaml)   
    
    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = context

    return context


def set_active_context(context: Context) -> None:
	""" 
	Set the active debuda context object. 
	
	Args:
		context (Context): Debuda context object.

	Notes:
		- Every new context initialization will overwrite the currently active context.
	"""
	global GLOBAL_CONTEXT
	GLOBAL_CONTEXT = context


def find_runtime_data_yaml_filename(output_dir: str = None) -> Union[str, None]:
	""" Find the runtime data yaml file in the output directory. If directory is not specified, try to find the most recent buda output directory.

	Args:	
		output_dir(str, optional): Path to the output directory.
	"""
	runtime_data_yaml_filename = f"{output_dir}/runtime_data.yaml"
	if not os.path.exists(runtime_data_yaml_filename):
		raise util.TTFatalException(f"Error: Yaml file at {runtime_data_yaml_filename} does not exist.")

	return runtime_data_yaml_filename


def locate_most_recent_build_output_dir() -> Union[str, None]:
	""" Try to find a default output directory. """
	most_recent_modification_time = None
	try:
		for tt_build_subfile in os.listdir("tt_build"):
			subdir = f"tt_build/{tt_build_subfile}"
			if os.path.isdir(subdir):
				if (
					most_recent_modification_time is None
					or os.path.getmtime(subdir) > most_recent_modification_time
				):
					most_recent_modification_time = os.path.getmtime(subdir)
					most_recent_subdir = subdir
		return most_recent_subdir
	except:
		return None
