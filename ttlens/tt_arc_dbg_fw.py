# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import os
import time
from typing import Union, List
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException
from ttlens.tt_lens_lib_utils import check_context, arc_read, arc_write, split_32bit_to_16bit
from ttlens.tt_lens_lib import arc_msg, read_words_from_device
from ttlens.tt_arc import load_arc_fw
from ttlens.tt_arc_dbg_fw_log_context import LogInfo, ArcDfwLogContext, ArcDfwLogContextFromList, ArcDfwLogContextFromYaml
from ttlens.tt_arc_dbg_fw_compiler import add_logging_instructions_to_arc_dbg_fw

DFW_MSG_CLEAR_DRAM         = 0x1  # Calls dfw_clear_drpam(start_addr, size)
DFW_MSG_CHECK_DRAM_CLEARED = 0x2  # Calls dfw_check_dram_cleared(start_addr, size)
DFW_MSG_SETUP_LOGGING      = 0x3  # Calls dfw_setup_log_buffer(start_addr, size)
DFW_MSG_SETUP_PMON         = 0x4  # Calls dfw_setup_pmon(pmon_id, ro_id)
DFW_MSG_RESET_FW           = 0x5  # Sends a message to put fw in reset state

DFW_DEFAULT_BUFFER_ADDR = 32

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
    "msg_arg1": 40
}

def modify_dfw_buffer_header(field: str,value: int, device_id: int, context: Context = None) -> None:
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
    if field not in DFW_BUFFER_HEADER_OFFSETS:
        raise TTException("Invalid field")

    context = check_context(context)
    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()    

    dfw_buffer_addr = arc_dbg_fw_get_buffer_start_addr(device_id, context)

    arc_write(context, device_id, arc_core_loc, dfw_buffer_addr + DFW_BUFFER_HEADER_OFFSETS[field], value)

def read_dfw_buffer_header(field: str, device_id: int, context: Context = None) -> int:
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
    if field not in DFW_BUFFER_HEADER_OFFSETS:
        raise TTException("Invalid field")

    context = check_context(context)
    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()    

    dfw_buffer_addr = arc_dbg_fw_get_buffer_start_addr(device_id, context)

    return arc_read(context, device_id, arc_core_loc, dfw_buffer_addr + DFW_BUFFER_HEADER_OFFSETS[field])

def send_buffer_addr_and_size_to_arc_dbg_fw(device_id: int, context: Context = None) -> None:
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

    MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR = 0xaa91
    MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE = 0xaa92
    timeout = 1000
    
    arg0, arg1 = split_32bit_to_16bit(DFW_DEFAULT_BUFFER_ADDR)
    response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_ADDR, True, arg0, arg1, timeout, context)

    if response[0] == -1:
        raise TTException("Newer version of ARC firmware required to support this feature")
    
    buffer_size = arc_dbg_fw_get_buffer_size()
    arg0, arg1 = split_32bit_to_16bit(buffer_size)
    response = arc_msg(device_id, MSG_TYPE_ARC_DBG_FW_DRAM_BUFFER_SIZE, True, arg0, arg1, timeout, context)

    if response[0] == -1:
        raise TTException("Arc msg error")
    

def arc_dbg_fw_get_buffer_start_addr(device_id: int = 0, context: Context = None) -> int:
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
    mcore_buffer_addr = arc_read(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"))
    
    if mcore_buffer_addr != 0:
        return mcore_buffer_addr

    # if mccore_buffer_addr is 0, then tt-metal is not running, so we will use the default address, and send the message to the debug buffer
    # with the default address and size
    send_buffer_addr_and_size_to_arc_dbg_fw(device_id, context)

    return DFW_DEFAULT_BUFFER_ADDR
     
def arc_dbg_fw_get_buffer_size() -> int:
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

def prepare_arc_dbg_fw(device_id: int = 0, context: Context = None) -> None:

    device = context.devices[device_id]
    
    # If tt-metal is running, it will alocate a buffer in the dram and give us the address where the buffer is stored
    mcore_buffer_addr = arc_read(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_MCORE_DBG_BUFFER_ADDR"))
    
    if mcore_buffer_addr == 0:
        # if mccore_buffer_addr is 0, then tt-metal is not running, so we will neet to send the message to the debug buffer
        # with the default address and size, so it can know where to send the messages
        send_buffer_addr_and_size_to_arc_dbg_fw(device_id, context)

def arc_dbg_fw_send_message(message, arg0: int = 0, arg1: int = 0, device_id: int = 0, context: Context=None) -> None:
    """ Send a message to the ARC debug firmware, using the buffer in the DRAM.
    
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

    modify_dfw_buffer_header("msg_arg0", arg0, device_id, context)
    modify_dfw_buffer_header("msg_arg1", arg1, device_id, context)
    assert(message & 0xffffff00 == 0) # "Message must be in the lower 8 bits"
    modify_dfw_buffer_header("msg", message | 0xabcdef00, device_id, context)

def read_arc_dfw_buffer2(device_id: int = 0, context: Context = None) -> List[int]:
    buffer_start_addr = arc_dbg_fw_get_buffer_start_addr(device_id, context) 
    buffer_size = len(DFW_BUFFER_HEADER_OFFSETS) * 4
    return read_words_from_device('ch0', device_id=device_id, addr=buffer_start_addr, word_count=buffer_size//4)

def arc_dbg_fw_check_msg_loop_running(device_id: int = 0, context: Context = None):
    """
    Send PING, check for PONG
    """
    context = check_context(context)

    device = context.devices[device_id]   

    arc_dbg_fw_send_message(0x88, 0, 0, device_id, context) 
    time.sleep(0.01) # Allow time for reply
    
    reply = read_dfw_buffer_header("msg", device_id, context)

    print(read_arc_dfw_buffer2(device_id,context))
    
    if (reply >> 16) != 0x99 or (reply & 0xff00) != 0x8800: 
        return False
    return True

def arc_dbg_fw_read_reply(device_id: int = 0, context: Context = None) -> int:
    """
    Read the reply from the ARC debug firmware.
    """
    context = check_context(context)

    return read_dfw_buffer_header("msg", device_id, context)>>16

def arc_dbg_fw_command(command: str, device_id: int = 0, context: Context = None) -> None:
    """
    Send a command to the ARC debug firmware. Available commands are "start", "stop", and "clear":
    """
    if not arc_dbg_fw_check_msg_loop_running(device_id, context):
        raise TTException("ARC debug firmware is not running.")

    DRAM_REGION_START_ADDR = arc_dbg_fw_get_buffer_start_addr(device_id, context)
    DRAM_REGION_SIZE = arc_dbg_fw_get_buffer_size()

    if command == "start":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DRAM_REGION_START_ADDR, DRAM_REGION_SIZE, device_id, context)
    elif command == "stop":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, 0xFFFFFFFF, 0xFFFFFFFF, device_id, context)
    elif command == "clear":
        arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DFW_MSG_CLEAR_DRAM, DRAM_REGION_SIZE, device_id, context)
    elif command == "reset":
        arc_dbg_fw_send_message(DFW_MSG_RESET_FW, 0, 0, device_id, context)


def setup_pmon(pmon_id, ro_id, wait_for_l1_trigger, stop_on_flatline, device_id: int = 0, context: Context = None):
    arg0 = pmon_id & 0xFF | (ro_id & 0xFF) << 8 | (wait_for_l1_trigger & 0xFF) << 16 | (stop_on_flatline & 0xFF) << 24
    print(
        f"Setting up PMON {pmon_id}, RO {ro_id}, wait_for_l1_trigger: {wait_for_l1_trigger}, stop_on_flatline: {stop_on_flatline} => {arg0:08x}"
    )
    arc_dbg_fw_send_message(DFW_MSG_SETUP_PMON, arg0, 0, device_id, context)

def load_arc_dbg_fw(file_name: str = "fw/arc/arc_dbg_fw.hex", log_context: ArcDfwLogContext = ArcDfwLogContextFromYaml("default"), device_id: int = 0, context: Context = None) -> None:
    """
    Loads the ARC debug firmware onto the specified device.
    This function constructs the path to the ARC debug firmware file, checks if it exists,
    prepares the device for firmware loading, and then loads the firmware onto the device.

    Args:
        file_name (str): The name of the ARC firmware file.
        log_yaml_location (str): The location of the log YAML file.
        device_id (int): The ID of the device to load the firmware onto.
        context (Context, optional): The context in which to load the firmware. Defaults to None.
    
    Raises:
        TTException: If the ARC firmware file does not exist.
    """
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", file_name)

    if not os.path.exists(file_path):
        raise TTException(f"ARC firmware file {file_path} does not exist.")

    if arc_dbg_fw_check_msg_loop_running(device_id, context):
        arc_dbg_fw_command("reset", device_id, context)
        reset_reply = arc_dbg_fw_read_reply(device_id, context)
        time.sleep(0.01)
        if reset_reply != 1:
            raise TTException("ARC debug firmware failed to reset.")

    name_of_modified_fw = "fw/arc/arc_modified.hex"
    add_logging_instructions_to_arc_dbg_fw(file_name, name_of_modified_fw, log_context)

    modified_fw_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", name_of_modified_fw)
    if not os.path.exists(modified_fw_file_path):
        raise TTException(f"ARC firmware file {modified_fw_file_path} does not exist.")
  
    prepare_arc_dbg_fw(device_id, context)

    load_arc_fw(modified_fw_file_path, 2, device_id, context)

    configure_arc_dbg_fw(log_context, device_id, context)

def configure_arc_dbg_fw(log_context: ArcDfwLogContext, device_id: int = 0, context: Context = None) -> None:
    device = context.devices[device_id]

    arc_write(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_RESET_SCRATCH2"), 0xbebaceca)
    arc_write(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_RESET_SCRATCH3"), 0xacafaca)
    arc_write(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_RESET_SCRATCH4"), 0xcecafaca)
    arc_write(context, device_id, device.get_arc_block_location(), device.get_register_addr("ARC_RESET_SCRATCH5"), 0xdeadbeef)

    modify_dfw_buffer_header("record_size_bytes", 4 * len(log_context.log_list), device_id, context)