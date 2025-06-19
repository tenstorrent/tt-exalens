# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cache
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.tensix_configuration_registers_description import TensixConfigurationRegistersDescription
from ttexalens.hardware.wormhole.arc_block import WormholeArcBlock
from ttexalens.hardware.wormhole.dram_block import WormholeDramBlock
from ttexalens.hardware.wormhole.eth_block import WormholeEthBlock
from ttexalens.hardware.wormhole.functional_worker_registers import configuration_registers_descriptions
from ttexalens.hardware.wormhole.functional_worker_block import WormholeFunctionalWorkerBlock
from ttexalens.hardware.wormhole.harvested_worker_block import WormholeHarvestedWorkerBlock
from ttexalens.hardware.wormhole.pcie_block import WormholePcieBlock
from ttexalens.hardware.wormhole.router_only_block import WormholeRouterOnlyBlock
import ttexalens.util as util
from ttexalens.device import TensixInstructions, Device


class WormholeInstructions(TensixInstructions):
    def __init__(self):
        import ttexalens.hw.tensix.wormhole.wormhole_ops as ops

        super().__init__(ops)


#
# Device
#
class WormholeDevice(Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)

    EFUSE_PCI = 0x1FF42200
    EFUSE_JTAG_AXI = 0x80042200
    EFUSE_NOC = 0x880042200

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = WormholeInstructions()

    def is_translated_coordinate(self, x: int, y: int) -> bool:
        return x >= 16 and y >= 16

    @cache
    def get_block(self, location: OnChipCoordinate) -> NocBlock:
        block_type = self.get_block_type(location)
        if block_type == "arc":
            return WormholeArcBlock(location)
        elif block_type == "dram":
            return WormholeDramBlock(location)
        elif block_type == "eth":
            return WormholeEthBlock(location)
        elif block_type == "functional_workers":
            return WormholeFunctionalWorkerBlock(location)
        elif block_type == "harvested_workers":
            return WormholeHarvestedWorkerBlock(location)
        elif block_type == "pcie":
            return WormholePcieBlock(location)
        elif block_type == "router_only":
            return WormholeRouterOnlyBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")

    def get_tensix_configuration_registers_description(self) -> TensixConfigurationRegistersDescription:
        return configuration_registers_descriptions


# end of class WormholeDevice
