# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import datetime
import os
import Pyro5.api
from typing import Sequence
import tt_umd

from ttexalens import util as util
from ttexalens.umd_device import UmdDevice


def create_simulation_cluster_descriptor(arch: tt_umd.ARCH) -> str:
    return f"""\
arch: {{
   0: {arch},
}}

chips: {{
   0: [0,0,0,0],
}}

ethernet_connections: [
]

chips_with_mmio: [
   0: 0,
]

# harvest_mask is the bit indicating which tensix row is harvested. So bit 0 = first tensix row; bit 1 = second tensix row etc...
harvesting: {{
   0: {{noc_translation: false, harvest_mask: 0}},
}}

# This value will be null if the boardtype is unknown, should never happen in practice but to be defensive it would be useful to throw an error on this case.
boardtype: {{
   0: {arch}Simulator,
}}
io_device_type: SIMULATION
"""


@Pyro5.api.expose
class UmdApi:
    @staticmethod
    def select_noc_id(noc_id: int, arch: tt_umd.ARCH | None = None):
        """
        Selects the NOC ID to be used for communication with the device by the current thread.
        This method should be called before any UMD API calls are made.
        """
        if noc_id == 0:
            tt_umd.set_thread_noc_id(tt_umd.NocId.NOC0)
        else:
            if arch == tt_umd.ARCH.QUASAR:
                tt_umd.set_thread_noc_id(tt_umd.NocId.SYSTEM_NOC)
            else:
                tt_umd.set_thread_noc_id(tt_umd.NocId.NOC1)

    def __init__(
        self,
        init_jtag=False,
        initialize_with_noc1=False,
        simulation_directory: str | None = None,
    ):
        self.devices: dict[int, UmdDevice] = {}

        UmdApi.select_noc_id(1 if initialize_with_noc1 else 0)
        if simulation_directory is not None:
            tt_umd.logging.set_level(tt_umd.logging.Level.Debug)
            tt_device = tt_umd.RtlSimulationTTDevice.create(simulation_directory)
            soc_descriptor = tt_device.get_soc_descriptor()
            # Fix for simulator
            for core in soc_descriptor.get_cores(tt_umd.CoreType.TENSIX):
                core_noc0 = soc_descriptor.translate_coord_to(core, tt_umd.CoordSystem.NOC0)
                tt_device.noc_write32(core_noc0.x, core_noc0.y, 0, 0x6F)
                tt_device.send_tensix_risc_reset(tt_umd.tt_xy_pair(core.x, core.y), deassert=True)
            self.devices[0] = UmdDevice(tt_device, 0, 0, soc_descriptor=soc_descriptor, is_simulation=True)
            cluster_descriptor_content = create_simulation_cluster_descriptor(self.devices[0].arch)
            self.cluster_descriptor = tt_umd.ClusterDescriptor.create_from_yaml_content(cluster_descriptor_content)
        else:
            # Respect UMD's existing env var first; default to ERROR otherwise.
            # If Python wants DEBUG, it can set TT_LOGGER_LEVEL=debug before calling into this function.
            if "TT_LOGGER_LEVEL" not in os.environ:
                tt_umd.logging.set_level(tt_umd.logging.Level.Error)

            discovery_options = tt_umd.TopologyDiscoveryOptions()
            discovery_options.io_device_type = tt_umd.IODeviceType.PCIe if not init_jtag else tt_umd.IODeviceType.JTAG
            # TODO: discovery_options.no_wait_for_eth_training = True
            # TODO: discovery_options.no_eth_firmware_strictness = True
            self.cluster_descriptor, devices = tt_umd.TopologyDiscovery.discover(discovery_options)

            if len(self.cluster_descriptor.get_all_chips()) == 0:
                raise RuntimeError("No Tenstorrent devices were detected on this system.")

            # Setup used devices
            unique_ids = self.cluster_descriptor.get_chip_unique_ids()
            for chip_id in self.cluster_descriptor.get_all_chips():
                device = devices[chip_id]
                unique_id = unique_ids.get(chip_id, None)
                assert unique_id is not None, f"Unique ID for device {chip_id} not found."

                if not self.cluster_descriptor.is_chip_mmio_capable(chip_id):
                    soc_descriptor = tt_umd.SocDescriptor(device)
                    mmio_chip_id = self.cluster_descriptor.get_closest_mmio_capable_chip(chip_id)
                    active_eth_channels = self.cluster_descriptor.get_active_eth_channels(mmio_chip_id)
                    active_eth_cores = soc_descriptor.get_eth_cores_for_channels(
                        active_eth_channels, tt_umd.CoordSystem.TRANSLATED
                    )
                    active_eth_coords_on_mmio_chip = [(core.x, core.y) for core in active_eth_cores]
                else:
                    active_eth_coords_on_mmio_chip = []

                wrapped_device = UmdDevice(device, chip_id, unique_id, active_eth_coords_on_mmio_chip)
                assert wrapped_device.is_mmio_capable == self.cluster_descriptor.is_chip_mmio_capable(chip_id)
                self.devices[chip_id] = wrapped_device
                self.devices[unique_id] = wrapped_device

    def get_device(self, chip_id: int) -> UmdDevice:
        if chip_id not in self.devices:
            raise RuntimeError(f"Device with chip id {chip_id} not found.")
        return self.devices[chip_id]

    def get_cluster_descriptor(self) -> tt_umd.ClusterDescriptor:
        return self.cluster_descriptor

    def warm_reset(self, noc_id: int, is_galaxy_configuration: bool = False) -> None:
        UmdApi.select_noc_id(noc_id)
        if is_galaxy_configuration:
            tt_umd.WarmReset.ubb_warm_reset()
        else:
            tt_umd.WarmReset.warm_reset()


def local_init(init_jtag=False, initialize_with_noc1=False, simulation_directory: str | None = None):
    if "TT_LOGGER_LEVEL" not in os.environ:
        if util.Verbosity.get() == util.Verbosity.DEBUG:
            os.environ["TT_LOGGER_LEVEL"] = "debug"
        elif util.Verbosity.get() == util.Verbosity.TRACE:
            os.environ["TT_LOGGER_LEVEL"] = "trace"

    communicator = UmdApi(init_jtag, initialize_with_noc1, simulation_directory)
    util.VERBOSE("Device opened successfully.")
    return communicator
