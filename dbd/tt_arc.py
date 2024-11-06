from typing import Union, List
from dbd.tt_debuda_context import Context
from dbd.tt_util import TTException
import re
import os

from dbd.tt_debuda_lib_utils import check_context, arc_read, arc_write

def run_arc_core(mask: int, device_id: int = 0, context: Context = None):
    """ Runs the arc core specified by the mask.

    Args:
        mask : Mask specifying which ARC core to run.
        device_id (int, default 0) : ID number of device to run ARC core on.
        context (Context, optional) : Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    context = check_context(context)
    
    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()

    # Write to bits 0-3
    reg_addr = device.get_register_addr("ARC_RESET_ARC_MISC_CNTL")
    
    # Read current value
    current = arc_read(context, device_id, arc_core_loc, reg_addr)
    # Clear bits 0-3 and set new value
    new_value = (current & ~0xF) | (mask & 0xF)
    arc_write(context, device_id, arc_core_loc, reg_addr, new_value)

    # Wait for acknowledgment
    core_run_ack = 0
    while (core_run_ack & mask != mask):
        status = arc_read(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_ARC_MISC_STATUS"))
        core_run_ack = status & 0xF  # Read bits 0-3

    # Clear control bits
    current = arc_read(context, device_id, arc_core_loc, reg_addr)
    arc_write(context, device_id, arc_core_loc, reg_addr, current & ~0xF)

def halt_arc_core(mask: int, device_id: int = 0, context: Context = None):
    """ Halts the ARC core specified by the mask.

    Args:
        mask : Mask specifying which ARC core to halt.
        device_id (int, default 0) : ID number of device to halt ARC core on.
        context (Context, optional) : Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    context = check_context(context)
    
    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()

    reg_addr = device.get_register_addr("ARC_RESET_ARC_MISC_CNTL")
    
    # Read current value
    current = arc_read(context, device_id, arc_core_loc, reg_addr)
    # Set bits 4-7 with mask
    new_value = (current & ~0xF0) | ((mask & 0xF) << 4)
    arc_write(context, device_id, arc_core_loc, reg_addr, new_value)

    # Wait for acknowledgment
    core_halt_ack = 0
    while (core_halt_ack != mask):
        status = arc_read(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_ARC_MISC_STATUS"))
        core_halt_ack = (status >> 4) & 0xF  # Read bits 4-7
    
    # Clear halt bits
    current = arc_read(context, device_id, arc_core_loc, reg_addr)
    arc_write(context, device_id, arc_core_loc, reg_addr, current & ~0xF0)

def set_udmiaxi_region(mem_type: str, device_id: int = 0, context:Context=None):
    """ Sets the UDMIAXI region to the specified memory type.

    Args:
        mem_type (str): Memory type to set the UDMIAXI region to. Can be 'iccm', 'iccm0', 'iccm1', 'iccm2', 'iccm3', or 'csm'.
        device_id (int, default 0): ID number of device to set UDMIAXI region on.
        context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    context = check_context(context)
    
    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()

    iccm_id = re.findall('\d',mem_type)
    if len(iccm_id) == 0:
        iccm_id = 0
        assert mem_type=='iccm' or mem_type=='csm'
    else:
        iccm_id = int(iccm_id[0])
        assert iccm_id>=0 and iccm_id<=3

    base_addr = ((0x10000000 >> 24) & 0xff) if mem_type == 'csm' else (iccm_id*0x3)

    arc_write(context, device_id, arc_core_loc, device.get_register_addr("ARC_RESET_ARC_UDMIAXI_REGION"), base_addr)

def load_arc_fw(file_name: str, iccm_id: int, device_id: int, context: Context = None) -> None:
    """ Loads the ARC firmware from the file into the device.

    Args:
        file_name (str): Path to the file containing the ARC firmware.
        iccm_id (int): ICCM ID to load the firmware into. Must be between 0 and 3.
        device_id (int, default 0): ID number of device to load firmware on.
        context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    # Check that iccm_id is valid
    if iccm_id not in range(4):
        raise TTException(f"Invalid ICCM ID {iccm_id}. Must be between 0 and 3.")

    # Check if the file exists
    if not os.path.exists(file_name):
        raise TTException(f"ARC firmware file {file_name} does not exist.")

    context = check_context(context)

    device = context.devices[device_id]
    arc_core_loc = device.get_arc_block_location()

    mem_type = f'iccm{iccm_id}'

    halt_arc_core(1<<iccm_id, device_id, context)

    set_udmiaxi_region(mem_type, device_id, context)

    base_addr = device.get_register_addr("ARC_CSM_DATA")

    def read_contiguous_hex_chunks(f):
        chunk_start_address = 0
        current_chunk = bytearray()

        for line in f:
            a = line.split ('@')
            if len(a)==2: # Address change
                # address change splits chunk, output current chunk if not empty
                if len(current_chunk) > 0:
                    yield (chunk_start_address, current_chunk)
                    current_chunk = []

                chunk_start_address = int (a[1], 16) * 4   # Parse hex number, hence 16
            else:         # Data
                data = int(a[0], 16)
                current_chunk += data.to_bytes(4, 'big')

        if len(current_chunk) > 0:
            yield (chunk_start_address, current_chunk)

    with open(file_name) as f:
        first_chunk = True

        for offset, data in read_contiguous_hex_chunks(f):
            if first_chunk: # Load reset vector
                word = int.from_bytes(data[0:4], 'little')
                arc_write(context, device_id, arc_core_loc, device.get_register_addr("ARC_ROM_DATA"), word)
                first_chunk = False

            for i in range(len(data) // 4):
                word = int.from_bytes(data[i*4 : i*4+4], 'little')
                arc_write(context, device_id, arc_core_loc, base_addr+i*4, word)

    set_udmiaxi_region("csm", device_id, context)
    run_arc_core(1<<iccm_id, device_id, context)