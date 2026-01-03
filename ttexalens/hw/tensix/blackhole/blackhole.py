# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cache
import tt_umd
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.blackhole.arc_block import BlackholeArcBlock
from ttexalens.hardware.blackhole.dram_block import BlackholeDramBlock
from ttexalens.hardware.blackhole.eth_block import BlackholeEthBlock
from ttexalens.hardware.blackhole.functional_worker_registers import tensix_registers_descriptions
from ttexalens.hardware.blackhole.functional_worker_debug_bus_signals import tensix_debug_bus_description
from ttexalens.hardware.blackhole.functional_worker_block import BlackholeFunctionalWorkerBlock
from ttexalens.hardware.blackhole.harvested_worker_block import BlackholeHarvestedWorkerBlock
from ttexalens.hardware.blackhole.harvested_eth_block import BlackholeHarvestedEthBlock
from ttexalens.hardware.blackhole.harvested_dram_block import BlackholeHarvestedDramBlock
from ttexalens.hardware.blackhole.l2cpu_block import BlackholeL2cpuBlock
from ttexalens.hardware.blackhole.pcie_block import BlackholePcieBlock
from ttexalens.hardware.blackhole.router_only_block import BlackholeRouterOnlyBlock
from ttexalens.hardware.blackhole.security_block import BlackholeSecurityBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.tensix_registers_description import TensixDebugBusDescription, TensixRegisterDescription
import ttexalens.util as util
from ttexalens.device import TensixInstructions, Device


class BlackholeInstructions(TensixInstructions):
    def __init__(self):
        import ttexalens.hw.tensix.blackhole.blackhole_ops as ops

        super().__init__(ops)


#
# Device
#
class BlackholeDevice(Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)

    def __init__(
        self,
        id: int,
        arch: tt_umd.ARCH,
        cluster_descriptor: tt_umd.ClusterDescriptor,
        soc_descriptor: tt_umd.SocDescriptor,
        context: Context,
    ):
        super().__init__(id, arch, cluster_descriptor, soc_descriptor, context)
        self.instructions = BlackholeInstructions()

    def is_blackhole(self) -> bool:
        return True

    @cache
    def get_block(self, location: OnChipCoordinate) -> NocBlock:
        block_type = self.get_block_type(location)
        if block_type == "arc":
            return BlackholeArcBlock(location)
        elif block_type == "dram":
            return BlackholeDramBlock(location)
        elif block_type == "harvested_dram":
            return BlackholeHarvestedDramBlock(location)
        elif block_type == "eth":
            return BlackholeEthBlock(location)
        elif block_type == "harvested_eth":
            return BlackholeHarvestedEthBlock(location)
        elif block_type == "functional_workers":
            return BlackholeFunctionalWorkerBlock(location)
        elif block_type == "harvested_workers":
            return BlackholeHarvestedWorkerBlock(location)
        elif block_type == "l2cpu":
            return BlackholeL2cpuBlock(location)
        elif block_type == "pcie":
            return BlackholePcieBlock(location)
        elif block_type == "router_only":
            return BlackholeRouterOnlyBlock(location)
        elif block_type == "security":
            return BlackholeSecurityBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")

    def get_tensix_registers_description(self) -> TensixRegisterDescription:
        return tensix_registers_descriptions

    def get_tensix_debug_bus_description(self) -> TensixDebugBusDescription:
        return tensix_debug_bus_description
