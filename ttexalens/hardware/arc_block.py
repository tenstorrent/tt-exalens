# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cached_property
import os
import re
from time import sleep
import tt_umd

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.util import FirmwareVersion, TTException

# For new firmware version (18.4 or higher) we have same telemetry tags for both wormhole and blackhole
# We no longer support ARC telemetry for firmware versions 18.3 and lower

CUTOFF_FIRMWARE_VERSION = FirmwareVersion(18, 4, 0)

telemetry_tags_map: dict[str, int] = {
    "BOARD_ID_HIGH": 1,
    "BOARD_ID_LOW": 2,
    "ASIC_ID": 3,
    "HARVESTING_STATE": 4,
    "UPDATE_TELEM_SPEED": 5,
    "VCORE": 6,
    "TDP": 7,
    "TDC": 8,
    "VDD_LIMITS": 9,
    "THM_LIMITS": 10,
    "ASIC_TEMPERATURE": 11,
    "VREG_TEMPERATURE": 12,
    "BOARD_TEMPERATURE": 13,
    "AICLK": 14,
    "AXICLK": 15,
    "ARCCLK": 16,
    "L2CPUCLK0": 17,
    "L2CPUCLK1": 18,
    "L2CPUCLK2": 19,
    "L2CPUCLK3": 20,
    "ETH_LIVE_STATUS": 21,
    "DDR_STATUS": 22,
    "DDR_SPEED": 23,
    "ETH_FW_VERSION": 24,
    "DDR_FW_VERSION": 25,
    "BM_APP_FW_VERSION": 26,
    "BM_BL_FW_VERSION": 27,
    "FLASH_BUNDLE_VERSION": 28,
    "CM_FW_VERSION": 29,
    "L2CPU_FW_VERSION": 30,
    "FAN_SPEED": 31,
    "TIMER_HEARTBEAT": 32,
    "TELEMETRY_ENUM_COUNT": 33,
    "ENABLED_TENSIX_COL": 34,
    "ENABLED_ETH": 35,
    "ENABLED_GDDR": 36,
    "ENABLED_L2CPU": 37,
    "PCIE_USAGE": 38,
    "NUMBER_OF_TAGS": 39,
    "ASIC_LOCATION": 52,
    "AICLK_LIMIT_MAX": 63,
}


class ArcBlock(NocBlock):
    def __init__(self, location: OnChipCoordinate, block_type: str):
        super().__init__(location, block_type)

    @cached_property
    def telemetry_tags(self) -> dict[str, int] | None:
        return telemetry_tags_map if self.location.device.firmware_version >= CUTOFF_FIRMWARE_VERSION else None

    @cached_property
    def telemetry_tag_ids(self) -> set[int] | None:
        return set(self.telemetry_tags.values()) if self.telemetry_tags else None

    def has_telemetry_tag_id(self, tag_id: int) -> bool:
        """Returns the keys of the ARC telemetry tags map."""
        if self.telemetry_tag_ids is None:
            raise TTException(
                f"We no longer support ARC telemetry for firmware versions 18.3 and lower. This device is running firmware version {self.location.device.firmware_version}"
            )
        return tag_id in self.telemetry_tag_ids

    def get_telemetry_tag_id(self, tag_name) -> int | None:
        """Returns the telemetry tag ID for a given tag name."""
        if self.telemetry_tags is None:
            raise TTException(
                f"We no longer support ARC telemetry for firmware versions 18.3 and lower. This device is running firmware version {self.location.device.firmware_version}"
            )
        if tag_name in self.telemetry_tags:
            return self.telemetry_tags[tag_name]
        return None

    def run_arc_core(self, mask: int):
        """Runs the arc core specified by the mask.

        Args:
            mask : Mask specifying which ARC core to run.
        """
        arc_register_store = self.get_register_store()

        # Write to bits 0-3

        # Read current value
        current = arc_register_store.read_register("ARC_RESET_ARC_MISC_CNTL")
        # Clear bits 0-3 and set new value
        new_value = (current & ~0xF) | (mask & 0xF)
        arc_register_store.write_register("ARC_RESET_ARC_MISC_CNTL", new_value)

        # Wait for acknowledgment
        core_run_ack = 0
        while core_run_ack & mask != mask:
            status = arc_register_store.read_register("ARC_RESET_ARC_MISC_STATUS")
            core_run_ack = status & 0xF  # Read bits 0-3

        # Clear control bits
        current = arc_register_store.read_register("ARC_RESET_ARC_MISC_CNTL")
        arc_register_store.write_register("ARC_RESET_ARC_MISC_CNTL", current & ~0xF)

    def halt_arc_core(self, mask: int):
        """Halts the ARC core specified by the mask.

        Args:
            mask : Mask specifying which ARC core to halt.
        """
        arc_register_store = self.get_register_store()

        # Read current value
        current = arc_register_store.read_register("ARC_RESET_ARC_MISC_CNTL")
        # Set bits 4-7 with mask
        new_value = (current & ~0xF0) | ((mask & 0xF) << 4)
        arc_register_store.write_register("ARC_RESET_ARC_MISC_CNTL", new_value)

        # Wait for acknowledgment
        core_halt_ack = 0
        while core_halt_ack != mask:
            status = arc_register_store.read_register("ARC_RESET_ARC_MISC_STATUS")
            core_halt_ack = (status >> 4) & 0xF  # Read bits 4-7

        # Clear halt bits
        current = arc_register_store.read_register("ARC_RESET_ARC_MISC_CNTL")
        arc_register_store.write_register("ARC_RESET_ARC_MISC_CNTL", current & ~0xF0)

    def set_udmiaxi_region(self, mem_type: str):
        """Sets the UDMIAXI region to the specified memory type.

        Args:
            mem_type (str): Memory type to set the UDMIAXI region to. Can be 'iccm', 'iccm0', 'iccm1', 'iccm2', 'iccm3', or 'csm'.
        """
        arc_register_store = self.get_register_store()

        iccm_id = re.findall("\d", mem_type)
        if len(iccm_id) == 0:
            iccm_id_int = 0
            assert mem_type == "iccm" or mem_type == "csm"
        else:
            iccm_id_int = int(iccm_id[0])
            assert iccm_id_int >= 0 and iccm_id_int <= 3

        base_addr = ((0x10000000 >> 24) & 0xFF) if mem_type == "csm" else (iccm_id_int * 0x3)

        # Additional bit needs to be set for blackhole, indicating that the udmiaxi region is going to be changed
        if self.device._arch == tt_umd.ARCH.BLACKHOLE:
            base_addr |= 0x100

        arc_register_store.write_register("ARC_RESET_ARC_UDMIAXI_REGION", base_addr)

    def trigger_fw_int(self) -> bool:
        """
        Triggers a firmware interrupt on the specified device.

        Args:
            device_id (int): The ID of the device to trigger the interrupt on. Defaults to 0.
            context (Context): The context containing device information. Defaults to None.
        Returns:
            bool: True if the interrupt was successfully triggered, False otherwise.
        """
        arc_register_store = self.get_register_store()

        misc = arc_register_store.read_register("ARC_RESET_ARC_MISC_CNTL")

        if misc & (1 << 16):
            return False

        misc_bit16_set = misc | (1 << 16)
        arc_register_store.write_register("ARC_RESET.ARC_MISC_CNTL", misc_bit16_set)

        return True

    def load_arc_fw(self, file_name: str, iccm_id: int) -> None:
        """Loads the ARC firmware from the file into the device.

        Args:
            file_name (str): Path to the file containing the ARC firmware.
            iccm_id (int): ICCM ID to load the firmware into. Must be between 0 and 3.
            device_id (int, default 0): ID number of device to load firmware on.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        """
        # Check that iccm_id is valid
        if iccm_id not in range(4):
            raise TTException(f"Invalid ICCM ID {iccm_id}. Must be between 0 and 3.")

        # Check if the file exists
        if not os.path.exists(file_name):
            raise TTException(f"ARC firmware file {file_name} does not exist.")

        arc_register_store = self.get_register_store()

        mem_type = f"iccm{iccm_id}"

        self.halt_arc_core(1 << iccm_id)

        if iccm_id == 0:
            MSG_TYPE_ARC_GO_TO_SLEEP = 0x55

            arc_register_store.write_register("ARC_RESET_SCRATCH5", 0xAA00 | MSG_TYPE_ARC_GO_TO_SLEEP)

            self.trigger_fw_int()
            sleep(0.01)  # Wait a bit for ARC to process this

        self.set_udmiaxi_region(mem_type)

        arc_csm_data = arc_register_store.get_register_description("ARC_CSM_DATA")

        def read_contiguous_hex_chunks(f):
            chunk_start_address = 0
            current_chunk = bytearray()

            for line in f:
                a = line.split("@")
                if len(a) == 2:  # Address change
                    # address change splits chunk, output current chunk if not empty
                    if len(current_chunk) > 0:
                        yield (chunk_start_address, current_chunk)
                        current_chunk = bytearray()

                    chunk_start_address = int(a[1], 16) * 4  # Parse hex number, hence 16
                else:  # Data
                    data = int(a[0], 16)
                    current_chunk += data.to_bytes(4, "big")

            if len(current_chunk) > 0:
                yield (chunk_start_address, current_chunk)

        with open(file_name) as f:
            first_chunk = True

            for offset, data in read_contiguous_hex_chunks(f):
                if first_chunk:  # Load reset vector
                    word = int.from_bytes(data[0:4], "little")
                    arc_register_store.write_register("ARC_ROM_DATA", word)
                    first_chunk = False

                for i in range(len(data) // 4):
                    word = int.from_bytes(data[i * 4 : i * 4 + 4], "little")
                    offset_csm_data = arc_csm_data.change_offset(i * 4)
                    arc_register_store.write_register(offset_csm_data, word)

        self.set_udmiaxi_region("csm")
        self.run_arc_core(1 << iccm_id)
