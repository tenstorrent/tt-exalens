import os

from enum import Enum

import tt_debuda_ifc
import tt_debuda_ifc_cache
import tt_util as util

from tt_debuda_context import Context, BudaContext, LimitedContext

class DebudaIfcType(Enum):
	# Ways to access the device
	DBD_LOCAL   = 0
	DBD_REMOTE  = 1
	DBD_SERVER  = 2
	DBD_CACHED  = 3


class DebudaIfcOptions:
	ip_address: str = "localhost"
	port: int = 5555


def init_debuda_local(
		output_dir_path: str = None,
		netlist_path: str = None,
		wanted_devices: list = [],
):
	""" Initializes debuda internals by creating the device interface and debuda context.
	Interfacing device is local, through pybind.

	Parameters
	----------
	output_dir_path : str, optional
		Path to the debuda run output directory. If None, debuda will be initialized in limited mode.
	netlist_path : str, optional
		Path to the netlist file.
	wanted_devices : list, optional
		List of device IDs we want to connect to. If empty, connect to all available devices.

	Returns
	-------
	Context
		Debuda context object.
	"""

	# Try to find runtime_data.yaml
	if output_dir_path:
		runtime_data_yaml_filename = f"{output_dir_path}/runtime_data.yaml"
		if not os.path.exists(runtime_data_yaml_filename):
			# We want to raise exception here - for limited context, output_dir_path should be None
			raise util.TTException(f"Error: Yaml file at {runtime_data_yaml_filename} does not exist.")
	else:
		runtime_data_yaml_filename = None
		
	debuda_ifc = tt_debuda_ifc.init_pybind(runtime_data_yaml_filename, output_dir_path, wanted_devices)
	runtime_data_yaml, cluster_desc_yaml = get_yamls(debuda_ifc)

	return load_context(debuda_ifc, netlist_path, runtime_data_yaml, cluster_desc_yaml)


def init_debuda_remote(
		ip_address: str = 'localhost',
		port: int = 5555,
):
	""" Initializes debuda internals by creating the device interface and debuda context.
	Interfacing device is done remotely through debuda client.

	Parameters
	----------
	ip_address : str, default 'localhost'
		IP address of the debuda server.
	port : int, default 5555
		Port number of the debuda server interface.

	Returns
	-------
	Context
		Debuda context object.
	"""

	debuda_ifc = tt_debuda_ifc.connect_to_server(ip_address, port)
	runtime_data_yaml, cluster_desc_yaml = get_yamls(debuda_ifc)

	return load_context(debuda_ifc, None, runtime_data_yaml, cluster_desc_yaml)


def init_debuda_cached(
		cache_path: str,
		netlist_path: str = None,
):
	""" Initializes debuda internals by reading cached session data. There is no connection to the device.
	Only cached commands are available.

	Parameters
	----------
	cache_path : str
		Path to the cache file.
	netlist_path : str, optional
		Path to the netlist file.
		
	Returns
	-------
	Context
		Debuda context object.
	"""

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
		util.TTFatalException("Debuda does not support cluster description. Cannot connect to device.")

	return runtime_data_yaml, cluster_desc_yaml


def load_context(
		server_ifc: tt_debuda_ifc.DbdCommunicator, 
		netlist_filepath: str, 
		runtime_data_yaml: util.YamlFile, 
		cluster_desc_yaml: util.YamlFile
) -> Context:
    run_dirpath = server_ifc.get_run_dirpath()
    if run_dirpath is None or runtime_data_yaml is None:
        return LimitedContext(server_ifc, cluster_desc_yaml)
    else:
        return BudaContext(server_ifc, netlist_filepath, run_dirpath, runtime_data_yaml, cluster_desc_yaml)


def find_runtime_data_yaml(output_dir: str = None):
	""" Find the runtime data yaml file in the output directory. If directory is not specified, try to find the most recent buda output directory.

	Parameters
	----------
	output_dir : str, optional
		Path to the output directory.
	"""
	# Try to determine the output directory
	runtime_data_yaml_filename = None
	if output_dir is None:  # Then try to find the most recent tt_build subdir
		most_recent_build_output_dir = locate_most_recent_build_output_dir()
		if most_recent_build_output_dir:
			util.INFO(
				f"Output directory not specified. Using most recently changed subdirectory of tt_build: {os.getcwd()}/{most_recent_build_output_dir}"
			)
			output_dir = most_recent_build_output_dir
		else:
			util.WARN(
				f"Output directory (output_dir) was not supplied and cannot be determined automatically. Continuing with limited functionality..."
			)
	# Try to load the runtime data from the output directory
	runtime_data_yaml_filename = f"{output_dir}/runtime_data.yaml"
	if not os.path.exists(runtime_data_yaml_filename):
		util.WARN(f"Error: Yaml file at {runtime_data_yaml_filename} does not exist.")
		runtime_data_yaml_filename = None

	return runtime_data_yaml_filename, output_dir


def locate_most_recent_build_output_dir():
# Finds the most recent build directory
	# Try to find a default output directory
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
		pass
	return None