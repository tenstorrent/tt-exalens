# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import datetime
import os
import Pyro5.api
from typing import Sequence
import tt_umd

from ttexalens import util as util
from ttexalens.context import NocId
from ttexalens.umd_device import UmdDevice


def create_simulation_cluster_descriptor(arch: tt_umd.ARCH) -> str:
    return f"""\
arch:
   0: {arch}

chips:
   0: [0,0,0,0]

ethernet_connections: []

chips_with_mmio:
   - 0: 0

# harvest_mask is the bit indicating which tensix row is harvested. So bit 0 = first tensix row; bit 1 = second tensix row etc...
harvesting: {{
   0: {{noc_translation: false, harvest_mask: 0}},
}}

# This value will be null if the boardtype is unknown, should never happen in practice but to be defensive it would be useful to throw an error on this case.
boards:
    -
        - board_id: 0x36000000000
        - board_type: UNKNOWN
        - chips:
            - 0
io_device_type: SIMULATION
"""


@Pyro5.api.expose
class UmdApi:
    @staticmethod
    def select_noc_id(noc_id: NocId, arch: tt_umd.ARCH | None = None):
        """
        Selects the NOC ID to be used for communication with the device by the current thread.
        This method should be called before any UMD API calls are made.
        """
        if noc_id == NocId.NOC0:
            tt_umd.set_thread_noc_id(tt_umd.NocId.NOC0)
        else:
            if arch == tt_umd.ARCH.QUASAR:
                tt_umd.set_thread_noc_id(tt_umd.NocId.SYSTEM_NOC)
            else:
                tt_umd.set_thread_noc_id(tt_umd.NocId.NOC1)

    def __init__(
        self,
        init_jtag=False,
        noc_id: NocId = NocId.NOC0,
        simulation_directory: str | None = None,
    ):
        self.devices: dict[int, UmdDevice] = {}

        # Respect UMD's existing environment variable for logging level.
        # If it's not set, set it based on ttexalens' verbosity level.
        # This allows users to control UMD logging through the TT_LOGGER_LEVEL environment variable if they want to,
        # while also providing a reasonable default based on ttexalens' verbosity settings.
        # By default, UMD logs only errors to avoid spamming the user with too much information,
        # but if the user has set ttexalens to a more verbose level, we will set UMD's logging level to match that.
        if "TT_LOGGER_LEVEL" not in os.environ:
            if util.Verbosity.get() == util.Verbosity.DEBUG:
                tt_umd.logging.set_level(tt_umd.logging.Level.Debug)
            elif util.Verbosity.get() == util.Verbosity.TRACE:
                tt_umd.logging.set_level(tt_umd.logging.Level.Trace)
            else:
                tt_umd.logging.set_level(tt_umd.logging.Level.Error)

        UmdApi.select_noc_id(noc_id)
        if simulation_directory is not None:
            tt_device: tt_umd.TTDevice
            if simulation_directory.endswith(".so"):
                tt_device = tt_umd.TTSimTTDevice.create(simulation_directory)
            else:
                tt_device = tt_umd.RtlSimulationTTDevice.create(simulation_directory)
            soc_descriptor = tt_device.get_soc_descriptor()
            # Fix for simulator: write an infinite-loop stub to each Tensix core's reset vector
            # and take all cores out of reset. Downstream test harnesses then re-assert specific
            # cores, load their ELFs, and re-deassert. This keeps cores from executing garbage
            # between tt-exalens init and the harness taking over.
            for core in soc_descriptor.get_cores(tt_umd.CoreType.TENSIX):
                core_noc0 = soc_descriptor.translate_coord_to(core, tt_umd.CoordSystem.NOC0)
                tt_device.noc_write32(core_noc0.x, core_noc0.y, 0, 0x6F)
                tt_device.send_tensix_risc_reset(
                    tt_umd.tt_xy_pair(core.x, core.y),
                    tt_umd.TensixSoftResetOptions.TENSIX_DEASSERT_SOFT_RESET,
                )
            self.devices[0] = UmdDevice(tt_device, 0, 0, soc_descriptor=soc_descriptor, is_simulation=True)
            cluster_descriptor_content = create_simulation_cluster_descriptor(self.devices[0].arch)
            self.cluster_descriptor = tt_umd.ClusterDescriptor.create_from_yaml_content(cluster_descriptor_content)
        else:

            discovery_options = tt_umd.TopologyDiscoveryOptions()
            discovery_options.cmfw_mismatch_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
            discovery_options.cmfw_unsupported_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
            discovery_options.eth_fw_mismatch_action = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
            discovery_options.unexpected_routing_firmware_config = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
            discovery_options.eth_fw_heartbeat_failure = tt_umd.TopologyDiscoveryOptions.Action.IGNORE
            discovery_options.wait_on_ethernet_link_training = True  # TODO: Set to False.

            self.cluster_descriptor, devices = tt_umd.TopologyDiscovery.discover(
                discovery_options, tt_umd.IODeviceType.PCIe if not init_jtag else tt_umd.IODeviceType.JTAG
            )

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

    def warm_reset(self, noc_id: NocId, is_galaxy_configuration: bool = False) -> None:
        UmdApi.select_noc_id(noc_id)
        if is_galaxy_configuration:
            tt_umd.WarmReset.ubb_warm_reset()
        else:
            tt_umd.WarmReset.warm_reset()


def local_init(init_jtag=False, noc_id: NocId = NocId.NOC0, simulation_directory: str | None = None):
    communicator = UmdApi(init_jtag, noc_id, simulation_directory)
    util.VERBOSE("Device opened successfully.")
    return communicator
