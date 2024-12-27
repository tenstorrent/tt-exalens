# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import os
import time
from typing import List
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_lens_lib_utils import check_context, arc_read, arc_write, split_32bit_to_16bit
from ttlens.tt_lens_lib import arc_msg, read_from_device
from ttlens.tt_arc import load_arc_fw
from abc import abstractmethod, ABC


class ArcDfwHeader:
    DFW_BUFFER_HEADER_OFFSETS = {
        "magic_marker": 0,
        "version": 4,
        "status": 8,
        "error": 12,
        "circular_buffer_size_bytes": 16,
        "circular_buffer_start_offset": 20,
        "record_size_bytes": 24,
        "num_log_calls": 28,
        "msg": 32,
        "msg_arg0": 36,
        "msg_arg1": 40,
        "pmon_size": 44,
        "log_delay": 48,
    }

    DFW_DEFAULT_BUFFER_ADDR = 32

    def write_to_field(self, field: str, value: int, device_id: int, context: Context = None) -> None:
        """
        Modifies the specified field in the DFW buffer header.

        Args:
            field (str): The field to modify.
            value (int): The value to set.
            device_id (int): The ID of the device.
            context (Context): The context in which the device operates. Defaults to None.

        Raises:
            TTException: If the field is invalid or if the value is invalid.
        """
        if field not in self.DFW_BUFFER_HEADER_OFFSETS:
            raise TTException("Invalid field")

        context = check_context(context)
        device = context.devices[device_id]
        arc_core_loc = device.get_arc_block_location()

        dfw_buffer_addr = self.get_buffer_start_addr(device_id, context)

        arc_write(context, device_id, arc_core_loc, dfw_buffer_addr + self.DFW_BUFFER_HEADER_OFFSETS[field], value)

    def read_from_field(self, field: str, device_id: int, context: Context = None) -> int:
        """
        Reads the specified field in the DFW buffer header.

        Args:
            field (str): The field to read.
            device_id (int): The ID of the device.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            int: The value of the specified field.

        Raises:
            TTException: If the field is invalid.
        """
        if field not in self.DFW_BUFFER_HEADER_OFFSETS:
            raise TTException("Invalid field")
        context = check_context(context)
        device = context.devices[device_id]
        arc_core_loc = device.get_arc_block_location()

        dfw_buffer_addr = self.get_buffer_start_addr(device_id, context)

        return arc_read(context, device_id, arc_core_loc, dfw_buffer_addr + self.DFW_BUFFER_HEADER_OFFSETS[field])

    def send_buffer_addr_and_size_to_arc_dbg_fw(self, device_id: int, context: Context = None) -> None:
        """
        Sends the buffer address and size to the ARC debug firmware.
        This function sends the default buffer address and the buffer size to the ARC debug firmware using arc_msg.
        Arc needs to have updated firmware to support this feature.

        Args:
            device_id (int): The ID of the device to which the message is sent.
            context (Any): The context in which the message is sent.

        Raises:
            TTException: If the ARC firmware does not support this feature or if there is an error in sending the message.
        """
        MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR = 0xAA91
        MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE = 0xAA92
        timeout = 1000

        arg0, arg1 = split_32bit_to_16bit(self.DFW_DEFAULT_BUFFER_ADDR)
        response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR, True, arg0, arg1, timeout, context)

        if response[0] == -1:
            raise TTException("Newer version of ARC firmware required to support this feature")

        buffer_size = self.get_buffer_size()
        arg0, arg1 = split_32bit_to_16bit(buffer_size)
        response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE, True, arg0, arg1, timeout, context)

        if response[0] == -1:
            raise TTException("Arc msg error")

    def get_buffer_start_addr(self, device_id: int = 0, context: Context = None) -> int:
        """
        Retrieves the start address of the debug buffer for the specified device.
        This function checks if the tt-metal is running and has allocated a buffer in the DRAM.
        If so, it returns the address where the buffer is stored. If tt-metal is not running,
        it uses a default address and sends the message to the debug buffer with the default
        address and size.

        Args:
            device_id (int): The ID of the device. Defaults to 0.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            int: The start address of the debug buffer.
        """

        context = check_context(context)

        device = context.devices[device_id]

        # If tt-metal is running, it will alocate a buffer in the dram and give us the address where the buffer is stored
        mcore_buffer_addr = arc_read(
            context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR")
        )

        if mcore_buffer_addr != 0:
            return mcore_buffer_addr

        # if mccore_buffer_addr is 0, then tt-metal is not running, so we will use the default address, and send the message to the debug buffer
        # with the default address and size
        try:
            self.send_buffer_addr_and_size_to_arc_dbg_fw(device_id, context)
        except TTException as e:
            # This is the mitagation where the device does not have the required firmware to support the feature
            print(str(e) + " Using default buffer address and size.")
            arc_write(
                context,
                device_id,
                device.get_arc_block_location(),
                device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"),
                self.DFW_DEFAULT_BUFFER_ADDR,
            )
            arc_write(
                context,
                device_id,
                device.get_arc_block_location(),
                device.get_register_addr("ARC_MCORE_DBG_BUFFER_SIZE"),
                self.get_buffer_size(),
            )

        return self.DFW_DEFAULT_BUFFER_ADDR

    def get_buffer_size(self) -> int:
        """
        Retrieves the buffer size for ARC debugging from the environment variable.
        This function fetches the value of the environment variable 'TT_METAL_ARC_DEBUG_BUFFER_SIZE',
        converts it to an integer, and returns it. If the environment variable is not set,
        it raises a TTException.

        Returns:
            int: The buffer size for ARC debugging.

        Raises:
            TTException: If the 'TT_METAL_ARC_DEBUG_BUFFER_SIZE' environment variable is not set.
        """

        buffer_size = os.getenv("TT_METAL_ARC_DEBUG_BUFFER_SIZE")

        if buffer_size is None:
            raise TTException("TT_METAL_ARC_DEBUG_BUFFER_SIZE is not set")

        return int(buffer_size)

    def get_header_size(self) -> int:
        return len(self.DFW_BUFFER_HEADER_OFFSETS) * 4

    def get_buffer_size_without_header(self) -> int:
        return self.get_buffer_size() - self.get_header_size()

    def get_buffer_usable_size_without_header(self, log_size: int) -> int:
        temp = self.get_buffer_size_without_header()
        temp -= temp % log_size
        return temp


class ArcDebugFw(ABC):
    def __init__(
        self,
        base_fw_file_path: str,
        base_fw_symbols_file_path: str,
        modified_fw_file_path: str,
        device_id: int = 0,
        context: Context = None,
    ):
        self.base_fw_file_path = base_fw_file_path
        self.base_fw_symbols_file_path = base_fw_symbols_file_path
        self.modified_fw_file_path = modified_fw_file_path
        self.device_id = device_id
        self.code_patcher = None

        self.context = check_context(context)
        self.buffer_header = ArcDfwHeader()

        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.base_fw_file_path)

        if not os.path.exists(file_path):
            raise TTException(f"ARC firmwapre file {file_path} does not exist.")

    DFW_MSG_CLEAR_DRAM = 0x1  # Calls dfw_clear_drpam(start_addr, size)
    DFW_MSG_CHECK_DRAM_CLEARED = 0x2  # Calls dfw_check_dram_cleared(start_addr, size)
    DFW_MSG_SETUP_LOGGING = 0x3  # Calls dfw_setup_log_buffer(start_addr, size)
    DFW_MSG_SETUP_PMON = 0x4  # Calls dfw_setup_pmon(pmon_id, ro_id)
    DFW_MSG_RESET_FW = 0x5  # Sends a message to put fw in reset state

    @abstractmethod
    def _configure_arc_dbg_fw(self) -> None:
        pass

    def __prepare_arc_dbg_fw(self) -> None:
        """
        Prepares the ARC debug firmware for logging by sending it a message of the default buffer address and size.

        Args:
            device_id (int): The ID of the device to prepare. Defaults to 0.
            context (Context): The context in which the device operates. Defaults to None.

        Raises:
            TTException: If the ARC debug firmware is not running.
        """
        device = self.context.devices[self.device_id]

        # If tt-metal is running, it will alocate a buffer in the dram and give us the address where the buffer is stored
        mcore_buffer_addr = arc_read(
            self.context,
            self.device_id,
            device.get_arc_block_location(),
            device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"),
        )

        if mcore_buffer_addr == 0:
            # if mccore_buffer_addr is 0, then tt-metal is not running, so we will neet to send the message to the debug buffer
            # with the default address and size, so it can know where to send the messages
            self.buffer_header.send_buffer_addr_and_size_to_arc_dbg_fw(self.device_id, self.context)

    def __reset_if_fw_already_running(self):
        """
        Reset the ARC debug firmware if it is already running.

        Raises:
            TTException: If the ARC debug firmware fails to reset.
        """
        ARC_DFW_MAGIC_MARKER = 0x12345678
        if self.buffer_header.read_from_field("magic_marker", self.device_id, self.context) == ARC_DFW_MAGIC_MARKER:
            # Because the main loop of the fw can be stuck on waiting log_delay cycles, we need to wait approximately
            # the time that it takes to finish the loop
            delay = self.buffer_header.read_from_field("log_delay", self.device_id, self.context)
            wait_time = (delay / 500000) * 0.01 if delay > 500000 else 0.01
        else:
            wait_time = 0.01

        if self.check_msg_loop_running(wait_time, self.device_id, self.context):
            self.send_command_to_fw("reset", self.device_id, self.context)

            time.sleep(wait_time)

            reset_reply = self.read_reply_from_fw(self.device_id, self.context)
            if reset_reply != 1:
                raise TTException("ARC debug firmware failed to reset.")

    def load(self):
        """
        Loads the arc debug firmware onto the chip.
        """
        self.__reset_if_fw_already_running()

        self.code_patcher.patch()

        self.__prepare_arc_dbg_fw()

        modified_fw_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.modified_fw_file_path)
        load_arc_fw(modified_fw_file_path, 2, self.device_id, self.context)

        reply = self.buffer_header.read_from_field("msg", self.device_id, self.context)
        if reply != 0xBEBACECA:
            raise TTException("ARC debug firmware failed to load, try reseting the card and try again")

        self._configure_arc_dbg_fw()

    def send_message_to_fw(
        self, message, arg0: int = 0, arg1: int = 0, device_id: int = 0, context: Context = None
    ) -> None:
        """Send a message to the ARC debug firmware, using the buffer in the DRAM.

        Args:
            message: Message to send. Must be in the lower 8 bits.
            arg0 (int, default 0): First argument to the message.
            arg1 (int, default 0): Second argument to the message.
            device_id (int, default 0): ID number of device to send message to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.
        """
        # // Message format in buffer_header[8]:
        # // +-----------+-----------+-----------+-----------+
        # // | 0xab      | 0xcd      | 0xef      | MSG_CODE  |
        # // +-----------+-----------+-----------+-----------+
        # // Message reply in buffer_header[8]:
        # // +-----------+-----------+-----------+-----------+
        # // |         REPLY         | MSG_CODE  | 0x00      |
        # // +-----------+-----------+-----------+-----------+
        context = check_context(context)

        self.buffer_header.write_to_field("msg_arg0", arg0, device_id, context)
        self.buffer_header.write_to_field("msg_arg1", arg1, device_id, context)
        assert message & 0xFFFFFF00 == 0  # "Message must be in the lower 8 bits"
        self.buffer_header.write_to_field("msg", message | 0xABCDEF00, device_id, context)

    def check_msg_loop_running(self, wait_time: float = 0.01, device_id: int = 0, context: Context = None):
        """
        Send PING, check for PONG
        """
        context = check_context(context)

        self.send_message_to_fw(0x88, 0, 0, device_id, context)
        time.sleep(wait_time)  # Allow time for reply

        reply = self.buffer_header.read_from_field("msg", device_id, context)

        if (reply >> 16) != 0x99 or (reply & 0xFF00) != 0x8800:
            return False
        return True

    def read_reply_from_fw(self, device_id: int = 0, context: Context = None) -> int:
        """
        Read the reply from the ARC debug firmware.
        """
        context = check_context(context)

        return self.buffer_header.read_from_field("msg", device_id, context) >> 16

    def send_command_to_fw(self, command: str, device_id: int = 0, context: Context = None) -> None:
        """
        Send a command to the ARC debug firmware. Available commands are "start", "stop", and "clear":
        """
        DRAM_REGION_START_ADDR = self.buffer_header.get_buffer_start_addr(device_id, context)
        DRAM_REGION_SIZE = self.buffer_header.get_buffer_size()

        if command == "start":
            self.send_message_to_fw(
                self.DFW_MSG_SETUP_LOGGING, DRAM_REGION_START_ADDR, DRAM_REGION_SIZE, device_id, context
            )
        elif command == "stop":
            self.send_message_to_fw(self.DFW_MSG_SETUP_LOGGING, 0xFFFFFFFF, 0xFFFFFFFF, device_id, context)
        elif command == "clear":
            self.send_message_to_fw(
                self.DFW_MSG_SETUP_LOGGING, self.DFW_MSG_CLEAR_DRAM, DRAM_REGION_SIZE, device_id, context
            )
        elif command == "reset":
            self.send_message_to_fw(self.DFW_MSG_RESET_FW, 0, 0, device_id, context)

    def read_arc_dfw_log_buffer(self, device_id: int = 0, context: Context = None) -> List[int]:
        """
        Read the log buffer from the ARC debug firmware.

        Args:
            device_id (int): The ID of the device to read the log buffer from.
            context (Context): The context in which the device operates. Defaults to None.

        Returns:
            List[int]: The log buffer.
        """
        buffer_start_addr = (
            self.buffer_header.get_buffer_start_addr(device_id, context) + self.buffer_header.get_header_size()
        )
        buffer_size = self.buffer_header.get_buffer_size() - self.buffer_header.get_header_size()
        return read_from_device("ch0", device_id=device_id, addr=buffer_start_addr, num_bytes=buffer_size)
