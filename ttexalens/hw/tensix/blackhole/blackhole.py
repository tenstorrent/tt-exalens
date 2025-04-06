# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttexalens.baby_risc_debug import BabyRiscLocation
from ttexalens.baby_risc_info import BabyRiscInfo
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hw.tensix.blackhole.baby_risc_debug import BlackholeBabyRiscDebug
from ttexalens.hw.tensix.blackhole.riscs_info import BriscInfo, Trisc0Info, Trisc1Info, Trisc2Info
from ttexalens.hw.tensix.wormhole.riscs_info import EriscInfo
from ttexalens.register_store import RegisterStore
from ttexalens.risc_debug import RiscDebug
from ttexalens.risc_info import RiscInfo
import ttexalens.util as util
from typing import List, Union
from ttexalens.device import (
    TensixInstructions,
    Device,
)
from ttexalens.hw.tensix.blackhole.tensix_debug_bus_signal_store import (
    debug_bus_signal_map as tensix_debug_bus_signal_map,
)
from ttexalens.hw.tensix.blackhole.arc_register_store import register_map_noc0 as arc_register_map_noc0, register_map_noc1 as arc_register_map_noc1
from ttexalens.hw.tensix.blackhole.eth_register_store import (
    register_map_noc0 as eth_register_map_noc0,
    register_map_noc1 as eth_register_map_noc1,
)
from ttexalens.hw.tensix.blackhole.dram_register_store import (
    register_map_noc0 as dram_register_map_noc0,
    register_map_noc1 as dram_register_map_noc1,
)
from ttexalens.hw.tensix.blackhole.harvested_tensix_register_store import (
    register_map_noc0 as harvested_tensix_register_map_noc0,
    register_map_noc1 as harvested_tensix_register_map_noc1,
)
from ttexalens.hw.tensix.blackhole.pcie_register_store import register_map as pcie_register_map
from ttexalens.hw.tensix.blackhole.router_only_register_store import register_map as router_only_register_map
from ttexalens.hw.tensix.blackhole.tensix_register_store import (
    register_map_noc0 as tensix_register_map_noc0,
    register_map_noc1 as tensix_register_map_noc1,
)


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
    DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    # TODO: For register block limits
    CONFIGURATION_REGISTER_END = 0xFFEFFFFF

    NUM_UNPACKERS = 2
    NUM_PACKERS = 1

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = BlackholeInstructions()

    def get_alu_config(self) -> List[dict]:
        return [
            {
                "Fpu_srnd_en": "ALU_ROUNDING_MODE_Fpu_srnd_en",
                "Gasket_srnd_en": "ALU_ROUNDING_MODE_Gasket_srnd_en",
                "Packer_srnd_en": "ALU_ROUNDING_MODE_Packer_srnd_en",
                "Padding": "ALU_ROUNDING_MODE_Padding",
                "GS_LF": "ALU_ROUNDING_MODE_GS_LF",
                "Bfp8_HF": "ALU_ROUNDING_MODE_Bfp8_HF",
                "SrcAUnsigned": "ALU_FORMAT_SPEC_REG0_SrcAUnsigned",
                "SrcBUnsigned": "ALU_FORMAT_SPEC_REG0_SrcBUnsigned",
                "Format_SrcA": "ALU_FORMAT_SPEC_REG0_SrcA",
                "Format_SrcB": "ALU_FORMAT_SPEC_REG1_SrcB",
                "Format_Dstacc": "ALU_FORMAT_SPEC_REG2_Dstacc",
                "Fp32_enabled": "ALU_ACC_CTRL_Fp32_enabled",
                "SFPU_Fp32_enabled": "ALU_ACC_CTRL_SFPU_Fp32_enabled",
                "INT8_math_enabled": "ALU_ACC_CTRL_INT8_math_enabled",
            }
        ]

    # UNPACKER GETTERS

    def get_unpack_tile_descriptor(self) -> List[dict]:
        struct_name = "UNPACK_TILE_DESCRIPTOR"
        fields = [
            "in_data_format",
            "uncompressed",
            "reserved_0",
            "blobs_per_xy_plane",
            "reserved_1",
            "x_dim",
            "y_dim",
            "z_dim",
            "w_dim",
            "blobs_y_start_lo",
            "blobs_y_start_hi",
            "digest_type",
            "digest_size",
        ]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_UNPACKERS)]

    def get_unpack_config(self) -> List[dict]:
        struct_name = "UNPACK_CONFIG"
        fields = [
            "out_data_format",
            "throttle_mode",
            "context_count",
            "haloize_mode",
            "tileize_mode",
            "unpack_src_reg_set_upd",
            "unpack_if_sel",
            "upsample_rate",
            "reserved_1",
            "upsample_and_interleave",
            "shift_amount",
            "uncompress_cntx0_3",
            "unpack_if_sel_cntx0_3",
            "force_shared_exp",
            "reserved_2",
            "uncompress_cntx4_7",
            "unpack_if_sel_cntx4_7",
            "reserved_3",
            "limit_addr",
            "reserved_4",
            "fifo_size",
            "reserved_5",
        ]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_UNPACKERS)]

    def get_pack_config(self) -> List[dict]:
        struct_name = "PACK_CONFIG"

        fields = [
            "row_ptr_section_size",
            "exp_section_size",
            "l1_dest_addr",
            "uncompress",
            "add_l1_dest_addr_offset",
            "disable_pack_zero_flag",
            "reserved_0",
            "out_data_format",
            "in_data_format",
            "dis_shared_exp_assembler",
            "auto_set_last_pacr_intf_sel",
            "enable_out_fifo",
            "sub_l1_tile_header_size",
            "src_if_sel",
            "pack_start_intf_pos",
            "all_pack_disable_zero_compress_ovrd",
            "add_tile_header_size",
            "pack_dis_y_pos_start_offset",
            "l1_src_addr",
        ]

        return [{field: f"{struct_name}{i}{j}_{field}" for field in fields} for i in [0] for j in [1]]

    def get_relu_config(self) -> List[dict]:

        return [
            {
                "disabled_src": "ALU_ACC_CTRL_Zero_Flag_disabled_src",
                "disabled_dst": "ALU_ACC_CTRL_Zero_Flag_disabled_dst",
                "apply_relu": "STACC_RELU_ApplyRelu",
                "relu_threshold": "STACC_RELU_ReluThreshold",
                "disable_main": "DISABLE_RISC_BP_Disable_main",
                "disable_trisc": "DISABLE_RISC_BP_Disable_trisc",
                "disable_ncrisc": "DISABLE_RISC_BP_Disable_ncrisc",
                "disable_bmp_clear_main": "DISABLE_RISC_BP_Disable_bmp_clear_main",
                "disable_bmp_clear_trisc": "DISABLE_RISC_BP_Disable_bmp_clear_trisc",
                "disable_bmp_clear_ncrisc": "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc",
            }
        ]

    def get_pack_dest_rd_ctrl(self) -> List[dict]:
        return [
            {
                "read_32b_data": "PACK_DEST_RD_CTRL_Read_32b_data",
                "read_unsigned": "PACK_DEST_RD_CTRL_Read_unsigned",
                "read_int8": "PACK_DEST_RD_CTRL_Read_int8",
                "round_10b_mant": "PACK_DEST_RD_CTRL_Round_10b_mant",
                "reserved": "PACK_DEST_RD_CTRL_Reserved",
            }
        ]

    def get_pack_edge_offset(self) -> List[dict]:
        struct_name = "PACK_EDGE_OFFSET"
        fields = [
            "mask",
            "mode",
            "tile_row_set_select_pack0",
            "tile_row_set_select_pack1",
            "tile_row_set_select_pack2",
            "tile_row_set_select_pack3",
        ]

        return [
            {field: f"{struct_name}{i}_{field}" for field in (fields if i == 0 else fields[:1])}
            for i in range(self.NUM_PACKERS)
        ]

    def get_pack_counters(self) -> List[dict]:
        struct_name = "PACK_COUNTERS"
        fields = [
            "pack_per_xy_plane",
            "pack_reads_per_xy_plane",
            "pack_xys_per_til",
            "pack_yz_transposed",
            "pack_per_xy_plane_offset",
        ]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_PACKERS)]

    def get_pack_strides(self) -> List[dict]:
        struct_name = "PACK_STRIDES"
        fields = ["x_stride", "y_stride", "z_stride", "w_stride"]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(2)]

    def _get_debug_bus_signal_store_for_block(
        self, block_type, location, neo_id=None
    ) -> Union[DebugBusSignalStore, None]:
        assert neo_id is None
        if block_type == "functional_workers":
            return DebugBusSignalStore(tensix_debug_bus_signal_map, location)
        return None

    def _get_register_store_for_block(
        self,
        block_type: str,
        location: OnChipCoordinate,
        noc_id: Union[int, None] = None,
        neo_id: Union[int, None] = None,
    ) -> Union[RegisterStore, None]:
        assert neo_id is None
        if block_type == "functional_workers":
            if noc_id == 0 or noc_id is None:
                return RegisterStore(tensix_register_map_noc0, location)
            elif noc_id == 1:
                return RegisterStore(tensix_register_map_noc1, location)
        elif block_type == "eth":
            if noc_id == 0 or noc_id is None:
                return RegisterStore(eth_register_map_noc0, location)
            elif noc_id == 1:
                return RegisterStore(eth_register_map_noc1, location)
        elif block_type == "harvested_workers":
            if noc_id == 0 or noc_id is None:
                return RegisterStore(harvested_tensix_register_map_noc0, location)
            elif noc_id == 1:
                return RegisterStore(harvested_tensix_register_map_noc1, location)
        elif block_type == "arc":
            if noc_id == 0 or noc_id is None:
                return RegisterStore(arc_register_map_noc0, location)
            elif noc_id == 1:
                return RegisterStore(arc_register_map_noc1, location)
        elif block_type == "dram":
            if noc_id == 0 or noc_id is None:
                return RegisterStore(dram_register_map_noc0, location)
            elif noc_id == 1:
                return RegisterStore(dram_register_map_noc1, location)
        # TODO: These hangs device :(
        # elif block_type == "pcie":
        #     if noc_id == 0 or noc_id is None:
        #         return RegisterStore(pcie_register_map, location)
        # elif block_type == "router_only":
        #     if noc_id == 0 or noc_id is None:
        #         return RegisterStore(router_only_register_map, location)
        return None

    def _get_risc_names_for_location(
        self, block_type: str, location: OnChipCoordinate, neo_id: Union[int, None] = None
    ) -> List[str]:
        assert neo_id is None
        if block_type == "functional_workers":
            return ["brisc", "trisc0", "trisc1", "trisc2"]
        elif block_type == "eth":
            return ["erisc"]
        return []

    def get_risc_debug(
        self,
        location: OnChipCoordinate,
        risc_name: str,
        noc_id: Union[int, None] = None,
        neo_id: Union[int, None] = None,
        verbose: bool = False,
    ) -> RiscDebug:
        assert neo_id is None
        if noc_id is None:
            noc_id = 0
        risc_name = risc_name.lower()
        risc_info: BabyRiscInfo = self.get_risc_info(location, risc_name, neo_id=neo_id)
        risc_location = BabyRiscLocation(location, risc_name, risc_id=risc_info.risc_id, noc_id=noc_id, neo_id=neo_id)
        return BlackholeBabyRiscDebug(risc_location, risc_info, verbose=verbose)

    def get_risc_info(self, location: OnChipCoordinate, risc_name: str, neo_id: Union[int, None] = None) -> RiscInfo:
        assert neo_id is None
        risc_name = risc_name.lower()
        block_type = self.get_block_type(location)
        if block_type == "functional_workers":
            if risc_name == "brisc":
                return BriscInfo()
            if risc_name == "trisc0":
                return Trisc0Info()
            if risc_name == "trisc1":
                return Trisc1Info()
            if risc_name == "trisc2":
                return Trisc2Info()
        elif block_type == "eth":
            if risc_name == "erisc":
                return EriscInfo()
        raise ValueError(f"Invalid risc name {risc_name} for block type {block_type} at {location.to_user_str()}.")
