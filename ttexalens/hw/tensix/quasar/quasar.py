# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache
import tt_umd
from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.quasar.functional_worker_block import QuasarFunctionalWorkerBlock
from ttexalens.hardware.tensix_registers_description import TensixDebugBusDescription, TensixRegisterDescription
from ttexalens.umd_device import UmdDevice

#
# Device
#
class QuasarDevice(Device):
    # TODO: Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    def __init__(self, id: int, umd_device: UmdDevice, context: Context):
        super().__init__(id, umd_device, context)

    def is_quasar(self) -> bool:
        return True

    @cache
    def get_block(self, location: OnChipCoordinate) -> NocBlock:
        block_type = self.get_block_type(location)
        if block_type == "functional_workers":
            return QuasarFunctionalWorkerBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")

    def get_tensix_registers_description(self) -> TensixRegisterDescription:
        raise NotImplementedError("Quasar does not have a Tensix registers description yet.")

    def get_tensix_debug_bus_description(self) -> TensixDebugBusDescription:
        raise NotImplementedError("Quasar does not have a Tensix debug bus description yet.")
