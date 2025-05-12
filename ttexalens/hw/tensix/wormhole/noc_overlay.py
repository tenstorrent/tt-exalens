# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
############################################################
# AUTO_GENERATED! DO NOT MODIFY!
# File was generated using scripts/noc_to_python/n2p.sh.
############################################################

from ctypes import LittleEndianStructure, c_uint32
from functools import cached_property
import struct

NOC_NUM_STREAMS = 64
ETH_NOC_NUM_STREAMS = 32
NOC_OVERLAY_START_ADDR = 0xFFB40000
NOC_STREAM_REG_SPACE_SIZE = 0x1000
NOC0_REGS_START_ADDR = 0xFFB20000
NOC1_REGS_START_ADDR = 0xFFB30000


def unpack_int(buffer: memoryview) -> int:
    int_value: int = struct.unpack_from("<I", buffer)[0]
    return int_value


class Noc_STREAM_REMOTE_SRC:
    """
    Properties of the remote source stream (coorindates, stream ID, and this streams destination index).
    Dont-care unless REMOTE_SOURCE == 1.
    """

    STREAM_REMOTE_SRC_X: int
    STREAM_REMOTE_SRC_Y: int
    REMOTE_SRC_STREAM_ID: int
    STREAM_REMOTE_SRC_DEST_INDEX: int
    DRAM_READS__TRANS_SIZE_WORDS_LO: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_REMOTE_SRC":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.STREAM_REMOTE_SRC_X = (value >> 0) & ((1 << 6) - 1)
        instance.STREAM_REMOTE_SRC_Y = (value >> 6) & ((1 << 6) - 1)
        instance.REMOTE_SRC_STREAM_ID = (value >> 12) & ((1 << 6) - 1)
        instance.STREAM_REMOTE_SRC_DEST_INDEX = (value >> 18) & ((1 << 6) - 1)
        instance.DRAM_READS__TRANS_SIZE_WORDS_LO = (value >> 12) & ((1 << 12) - 1)
        return instance


class Noc_STREAM_REMOTE_SRC_PHASE(LittleEndianStructure):
    """
    Remote source phase (may be different from the destination stream phase.)
    We use 20-bit phase ID, so phase count doesnt wrap until 1M phases.
    Dont-care unless REMOTE_SOURCE == 1.
    """

    DRAM_READS__SCRATCH_1_PTR: int
    DRAM_READS__TRANS_SIZE_WORDS_HI: int
    _fields_ = [
        ("DRAM_READS__SCRATCH_1_PTR", c_uint32, 19),
        ("DRAM_READS__TRANS_SIZE_WORDS_HI", c_uint32, 1),
    ]


class Noc_STREAM_REMOTE_DEST(LittleEndianStructure):
    """
    Properties of the remote destination stream (coorindates, stream ID).  Dont-care unless REMOTE_RECEIVER == 1.
    If destination is multicast, this register specifies the starting coordinates of the destination
    multicast group/rectangle. (The end coordinates are in STREAM_MCAST_DEST below.)
    """

    STREAM_REMOTE_DEST_X: int
    STREAM_REMOTE_DEST_Y: int
    STREAM_REMOTE_DEST_STREAM_ID: int
    _fields_ = [
        ("STREAM_REMOTE_DEST_X", c_uint32, 6),
        ("STREAM_REMOTE_DEST_Y", c_uint32, 6),
        ("STREAM_REMOTE_DEST_STREAM_ID", c_uint32, 6),
    ]


class Noc_STREAM_LOCAL_DEST(LittleEndianStructure):
    """
    Properties of the local destination gather stream connection.
    Dont-care unless LOCAL_RECEIVER == 1.
    Shares register space with STREAM_REMOTE_DEST_REG_INDEX.
    """

    STREAM_LOCAL_DEST_MSG_CLEAR_NUM: int
    STREAM_LOCAL_DEST_STREAM_ID: int
    _fields_ = [
        ("STREAM_LOCAL_DEST_MSG_CLEAR_NUM", c_uint32, 12),
        ("STREAM_LOCAL_DEST_STREAM_ID", c_uint32, 6),
    ]


class Noc_STREAM_REMOTE_DEST_BUF_START(LittleEndianStructure):
    """
    Start address (in words) of the remote destination stream memory buffer.
    """

    DRAM_WRITES__SCRATCH_1_PTR_LO: int
    _fields_ = [
        ("DRAM_WRITES__SCRATCH_1_PTR_LO", c_uint32, 16),
    ]


class Noc_STREAM_REMOTE_DEST_BUF_SIZE:
    """
    Size (in words) of the remote destination stream memory buffer.
    """

    REMOTE_DEST_BUF_SIZE_WORDS: int
    DRAM_WRITES__SCRATCH_1_PTR_HI: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_REMOTE_DEST_BUF_SIZE":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.REMOTE_DEST_BUF_SIZE_WORDS = (value >> 0) & ((1 << 17) - 1)
        instance.DRAM_WRITES__SCRATCH_1_PTR_HI = (value >> 0) & ((1 << 3) - 1)
        return instance


class Noc_STREAM_MISC_CFG(LittleEndianStructure):
    """
    The ID of NOCs used for incoming and outgoing data, followed by misc. stream configuration options:
      * Source - set exactly one of these to 1:
           SOURCE_ENDPOINT = source is local math/packer
           REMOTE_SOURCE = source is remote sender stream
           LOCAL_SOURCES_CONNECTED = source is one or more local connected streams
      * Destination - set one or zero of these to 1:
           RECEIVER_ENDPOINT = stream is read by local unpacker/math
           REMOTE_RECEIVER = stream forwards data to a remote destination or multicast group
           LOCAL_RECEIVER = stream is connected to a local destination stream
           None set = stream just stores data in a local buffer, without forwarding/clearing, and
                      finishes the phase once all messages have been received
      * Phase/data forward options:
         PHASE_AUTO_CONFIG = set to 1 for stream to fetch next phase configuration automatically.
         PHASE_AUTO_ADVANCE = set to 1 for stream to advance to next phase automatically
               (otherwise need to write STREAM_PHASE_ADVANCE below)
         DATA_AUTO_SEND = set to 1 to forward data automatically based on read/write pointers;
                set to 0 to forward data only when STREAM_NEXT_MSG_SEND is written
    """

    INCOMING_DATA_NOC: int
    OUTGOING_DATA_NOC: int
    REMOTE_SRC_UPDATE_NOC: int
    LOCAL_SOURCES_CONNECTED: int
    SOURCE_ENDPOINT: int
    REMOTE_SOURCE: int
    RECEIVER_ENDPOINT: int
    LOCAL_RECEIVER: int
    REMOTE_RECEIVER: int
    PHASE_AUTO_CONFIG: int
    PHASE_AUTO_ADVANCE: int
    DATA_AUTO_SEND: int
    NEXT_PHASE_SRC_CHANGE: int
    NEXT_PHASE_DEST_CHANGE: int
    DATA_BUF_NO_FLOW_CTRL: int
    """
    set if REMOTE_SOURCE==1 and the buffer is large enough to accept full phase data without wrapping:
    """

    DEST_DATA_BUF_NO_FLOW_CTRL: int
    """
    set if REMOTE_RECEIVER==1 and the destination buffer is large enough to accept full phase data without wrapping:
    """

    REMOTE_SRC_IS_MCAST: int
    """
    set if REMOTE_SOURCE==1 and has mulicast enabled (i.e. this stream is part of a multicast group)
    """

    NO_PREV_PHASE_OUTGOING_DATA_FLUSH: int
    """
    set if no need to flush outgoing remote data from previous phase
    """

    UNICAST_VC_REG: int
    """
    set to one of the values (0-5) to select which VC unicast requests will be sent on
    """

    REG_UPDATE_VC_REG: int
    """
    set to one of the values (0-5) to select which VC control flow updates will be sent on
    """

    _fields_ = [
        ("INCOMING_DATA_NOC", c_uint32, 1),
        ("OUTGOING_DATA_NOC", c_uint32, 1),
        ("REMOTE_SRC_UPDATE_NOC", c_uint32, 1),
        ("LOCAL_SOURCES_CONNECTED", c_uint32, 1),
        ("SOURCE_ENDPOINT", c_uint32, 1),
        ("REMOTE_SOURCE", c_uint32, 1),
        ("RECEIVER_ENDPOINT", c_uint32, 1),
        ("LOCAL_RECEIVER", c_uint32, 1),
        ("REMOTE_RECEIVER", c_uint32, 1),
        ("PHASE_AUTO_CONFIG", c_uint32, 1),
        ("PHASE_AUTO_ADVANCE", c_uint32, 1),
        ("DATA_AUTO_SEND", c_uint32, 1),
        ("NEXT_PHASE_SRC_CHANGE", c_uint32, 1),
        ("NEXT_PHASE_DEST_CHANGE", c_uint32, 1),
        ("DATA_BUF_NO_FLOW_CTRL", c_uint32, 1),
        ("DEST_DATA_BUF_NO_FLOW_CTRL", c_uint32, 1),
        ("REMOTE_SRC_IS_MCAST", c_uint32, 1),
        ("NO_PREV_PHASE_OUTGOING_DATA_FLUSH", c_uint32, 1),
        ("UNICAST_VC_REG", c_uint32, 3),
        ("REG_UPDATE_VC_REG", c_uint32, 3),
    ]


class Noc_STREAM_MCAST_DEST(LittleEndianStructure):
    """
    Destination spec for multicasting streams. STREAM_MCAST_END_X/Y are
    the end coordinate for the multicast rectangle, with the ones from
    STREAM_REMOTE_DEST taken as start.
    Dont-care if STREAM_MCAST_EN == 0.
    """

    STREAM_MCAST_END_X: int
    STREAM_MCAST_END_Y: int
    STREAM_MCAST_EN: int
    STREAM_MCAST_LINKED: int
    STREAM_MCAST_VC: int
    """
    Set to 0 to select VC 4, and 1 to select VC 5 (default 0)
    """

    STREAM_MCAST_NO_PATH_RES: int
    STREAM_MCAST_XY: int
    _fields_ = [
        ("STREAM_MCAST_END_X", c_uint32, 6),
        ("STREAM_MCAST_END_Y", c_uint32, 6),
        ("STREAM_MCAST_EN", c_uint32, 1),
        ("STREAM_MCAST_LINKED", c_uint32, 1),
        ("STREAM_MCAST_VC", c_uint32, 1),
        ("STREAM_MCAST_NO_PATH_RES", c_uint32, 1),
        ("STREAM_MCAST_XY", c_uint32, 1),
    ]


class Noc_STREAM_GATHER(LittleEndianStructure):
    """
    Specifies MSG_ARB_GROUP_SIZE. Valid values are 1 (round-robin
    arbitration between each incoming stream) or 4 (round-robin arbitration
    between groups of 4 incoming streams).
    """

    MSG_ARB_GROUP_SIZE: int
    MSG_SRC_IN_ORDER_FWD: int
    _fields_ = [
        ("MSG_ARB_GROUP_SIZE", c_uint32, 3),
        ("MSG_SRC_IN_ORDER_FWD", c_uint32, 1),
    ]


class Noc_STREAM_MSG_HEADER_FORMAT(LittleEndianStructure):
    """
    Offset & size of the size field in the message header. Only valid offsets are multiples of 8
    (i.e. byte-aligned).
    """

    MSG_HEADER_WORD_CNT_OFFSET: int
    MSG_HEADER_WORD_CNT_BITS: int
    _fields_ = [
        ("MSG_HEADER_WORD_CNT_OFFSET", c_uint32, 7),
        ("MSG_HEADER_WORD_CNT_BITS", c_uint32, 7),
    ]


class Noc_STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO(LittleEndianStructure):
    """
    For endpoints with SOURCE_ENDPOINT == 1, this register is for firmware
    to register new message for sending.
    This updates the msg_info register structure directly, rather than writing to the message info
    buffer in memory.
    Must not be written when the message info register structure is full, or if
    there are message info entries in the memory buffer. (This would cause a race
    condition.)
    """

    SOURCE_ENDPOINT_NEW_MSG_ADDR: int
    SOURCE_ENDPOINT_NEW_MSG_SIZE: int
    _fields_ = [
        ("SOURCE_ENDPOINT_NEW_MSG_ADDR", c_uint32, 17),
        ("SOURCE_ENDPOINT_NEW_MSG_SIZE", c_uint32, 15),
    ]


class Noc_STREAM_NUM_MSGS_RECEIVED_INC(LittleEndianStructure):
    """
    For endpoints with SOURCE_ENDPOINT == 1, this register is for firmware
    to update the number of messages whose data & header are available in the memory buffer.
    Hardware register is incremented atomically if sending of previous messages is in progress.
    """

    SOURCE_ENDPOINT_NEW_MSGS_NUM: int
    SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE: int
    _fields_ = [
        ("SOURCE_ENDPOINT_NEW_MSGS_NUM", c_uint32, 12),
        ("SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE", c_uint32, 17),
    ]


class Noc_STREAM_DEST_PHASE_READY_UPDATE(LittleEndianStructure):
    """
    Write phase number to indicate destination ready for the given phase.
    (This is done automatically by stream hardware when starting a phase with REMOTE_SOURCE=1.)
    The phase number is the one indicated by STREAM_REMOTE_SRC_PHASE_REG at destination.
    This register is mapped to the shared destination ready table, not a per-stream register.
    (Stream index is taken from the register address, and stored into the table along with the
    phase number.)
    """

    PHASE_READY_DEST_NUM: int
    PHASE_READY_NUM: int
    PHASE_READY_MCAST: int
    """
    set if this stream is part of multicast group (i.e. if REMOTE_SRC_IS_MCAST==1)
    """

    PHASE_READY_TWO_WAY_RESP: int
    """
    set if the message is in response to 2-way handshake
    """

    _fields_ = [
        ("PHASE_READY_DEST_NUM", c_uint32, 6),
        ("PHASE_READY_NUM", c_uint32, 20),
        ("PHASE_READY_MCAST", c_uint32, 1),
        ("PHASE_READY_TWO_WAY_RESP", c_uint32, 1),
    ]


class Noc_STREAM_SRC_READY_UPDATE(LittleEndianStructure):
    """
    Source ready message register for two-way handshake (sent by source in
    case destination ready entry is not found in the table).
    If received by a stream that already sent its ready update, it prompts resending.
    """

    STREAM_REMOTE_RDY_SRC_X: int
    STREAM_REMOTE_RDY_SRC_Y: int
    REMOTE_RDY_SRC_STREAM_ID: int
    _fields_ = [
        ("STREAM_REMOTE_RDY_SRC_X", c_uint32, 6),
        ("STREAM_REMOTE_RDY_SRC_Y", c_uint32, 6),
        ("REMOTE_RDY_SRC_STREAM_ID", c_uint32, 6),
    ]


class Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE(LittleEndianStructure):
    """
    Update available buffer space at remote destination stream.
    this is rd_ptr increment issued when a message is forwarded
    """

    REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_DEST_NUM: int
    REMOTE_DEST_BUF_WORDS_FREE_INC: int
    _fields_ = [
        ("REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_DEST_NUM", c_uint32, 6),
        ("REMOTE_DEST_BUF_WORDS_FREE_INC", c_uint32, 17),
    ]


class Noc_STREAM_WAIT_STATUS(LittleEndianStructure):
    """
    Status info for the stream.
    """

    WAIT_SW_PHASE_ADVANCE_SIGNAL: int
    """
    Set when stream is in START state with auto-config disabled, or if auto-config is enabled
    but PHASE_AUTO_ADVANCE=0
    """

    WAIT_PREV_PHASE_DATA_FLUSH: int
    """
    Set when stream has configured the current phase, but waits data from the previous one to be flushed.
    """

    MSG_FWD_ONGOING: int
    """
    Set when stream is in data forwarding state.
    """

    STREAM_CURR_STATE: int
    _fields_ = [
        ("WAIT_SW_PHASE_ADVANCE_SIGNAL", c_uint32, 1),
        ("WAIT_PREV_PHASE_DATA_FLUSH", c_uint32, 1),
        ("MSG_FWD_ONGOING", c_uint32, 1),
        ("STREAM_CURR_STATE", c_uint32, 4),
    ]


class Noc_STREAM_PHASE_AUTO_CFG_HEADER(LittleEndianStructure):
    """
    Register corresponding to the auto-configuration header. Written by each auto-config access
    at phase start, can be also written by software for initial configuration or if auto-config
    is disabled.
    PHASE_NUM_INCR is phase number increment relative to the previous executed phase (or 0 right
    after reset). The increment happens after auto-config is done, and before the phase is executed.
    (Therefore reading  STREAM_CURR_PHASE_REG while auto-config is ongoing, or if it hasnt started
    yet, may return the old phase number.)
    This enables up to 2^12-1 phases to be skipped. If more phases need to be skipped, it is
    necessary to insert an intermediate phase with zero messages, whose only purpose is to provide
    an additional skip offset.
    """

    PHASE_NUM_INCR: int
    CURR_PHASE_NUM_MSGS: int
    NEXT_PHASE_NUM_CFG_REG_WRITES: int
    _fields_ = [
        ("PHASE_NUM_INCR", c_uint32, 12),
        ("CURR_PHASE_NUM_MSGS", c_uint32, 12),
        ("NEXT_PHASE_NUM_CFG_REG_WRITES", c_uint32, 8),
    ]


class Noc_STREAM_PERF_CONFIG(LittleEndianStructure):
    """
    Should be written only for stream 0, applies to all streams.
    """

    CLOCK_GATING_EN: int
    CLOCK_GATING_HYST: int
    PARTIAL_SEND_WORDS_THR: int
    """
    PARTIAL_SEND_WORDS_THR contols the minimum number of 16-byte words of a tile to accumulate in a relay stream before sending it off to the destination.
    If the size of the tile is less than or equal to PARTIAL_SEND_WORDS_THR, then this feild is ignored.
    Default is 16 words
    """

    _fields_ = [
        ("CLOCK_GATING_EN", c_uint32, 1),
        ("CLOCK_GATING_HYST", c_uint32, 7),
        ("PARTIAL_SEND_WORDS_THR", c_uint32, 8),
    ]


class Noc_STREAM_GATHER_CLEAR(LittleEndianStructure):
    """
    Msg_LOCAL_STREAM_CLEAR_NUM specifies the number of messages that should
    be cleared from a gather stream before moving onto the next stream.
    When MSG_ARB_GROUP_SIZE > 1, the order of clearing the streams can be selected
    with MSG_GROUP_STREAM_CLEAR_TYPE. 0 = clear the whole group MSG_LOCAL_STREAM_CLEAR_NUM times,
    1 = clear each stream of the group MSG_LOCAL_STREAM_CLEAR_NUM times before
    moving onto the next stream in the group.
    """

    MSG_LOCAL_STREAM_CLEAR_NUM: int
    MSG_GROUP_STREAM_CLEAR_TYPE: int
    _fields_ = [
        ("MSG_LOCAL_STREAM_CLEAR_NUM", c_uint32, 16),
        ("MSG_GROUP_STREAM_CLEAR_TYPE", c_uint32, 1),
    ]


class Noc_STREAM_DEBUG_STATUS_SEL(LittleEndianStructure):
    """
    Debug bus stream selection. Write the stream id for the stream that you want exposed on the debug bus
    This register only exists in stream 0.
    """

    DEBUG_STATUS_STREAM_ID_SEL: int
    DISABLE_DEST_READY_TABLE: int
    _fields_ = [
        ("DEBUG_STATUS_STREAM_ID_SEL", c_uint32, 6),
        ("DISABLE_DEST_READY_TABLE", c_uint32, 1),
    ]


class Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE(LittleEndianStructure):
    """
    Available buffer space at remote destination stream(s).
    Dont care unless REMOTE_RECEIVER == 1.
    Source cant send data unless WORDS_FREE > 0.
    Read-only; updated automatically to maximum value when
    STREAM_REMOTE_DEST_BUF_SIZE_REG is updated.
    For multicast streams, values for successive destinations are at
    subsequent indexes (STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX+1,
    STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX+2, etc.).
    """

    REMOTE_DEST_WORDS_FREE: int
    _fields_ = [
        ("REMOTE_DEST_WORDS_FREE", c_uint32, 17),
    ]


class Noc_STREAM_BLOB_NEXT_AUTO_CFG_DONE:
    """
    Reading this register will give you a stream id of a stream that finished its blob (according to STREAM_BLOB_AUTO_CFG_DONE_REG_INDEX)
    Subsequent reads will give you the next stream, untill all streams are read, after which it will loop
    This register is only valid if BLOB_NEXT_AUTO_CFG_DONE_VALID is set (i.e. if STREAM_BLOB_AUTO_CFG_DONE_REG_INDEX non-zero)
    Exists only in stream 0
    """

    BLOB_NEXT_AUTO_CFG_DONE_STREAM_ID: int
    BLOB_NEXT_AUTO_CFG_DONE_VALID: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_BLOB_NEXT_AUTO_CFG_DONE":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.BLOB_NEXT_AUTO_CFG_DONE_STREAM_ID = (value >> 0) & ((1 << 6) - 1)
        instance.BLOB_NEXT_AUTO_CFG_DONE_VALID = (value >> 16) & ((1 << 1) - 1)
        return instance


class Noc_STREAM_SCRATCH_0(LittleEndianStructure):
    NCRISC_TRANS_EN: int
    NCRISC_TRANS_EN_IRQ_ON_BLOB_END: int
    NCRISC_CMD_ID: int
    NEXT_NRISC_PIC_INT_ON_PHASE: int
    """
    Kept for compatibility with grayskull, but doesnt not exist anymore in wormhole
    """

    _fields_ = [
        ("NCRISC_TRANS_EN", c_uint32, 1),
        ("NCRISC_TRANS_EN_IRQ_ON_BLOB_END", c_uint32, 1),
        ("NCRISC_CMD_ID", c_uint32, 3),
        ("NEXT_NRISC_PIC_INT_ON_PHASE", c_uint32, 19),
    ]


class Noc_STREAM_SCRATCH_1:
    DRAM_FIFO_RD_PTR_WORDS_LO: int
    NCRISC_LOOP_COUNT: int
    NCRISC_INIT_ENABLE_BLOB_DONE_IRQ: int
    NCRISC_INIT_DISABLE_BLOB_DONE_IRQ: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_SCRATCH_1":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.DRAM_FIFO_RD_PTR_WORDS_LO = (value >> 0) & ((1 << 24) - 1)
        instance.NCRISC_LOOP_COUNT = (value >> 0) & ((1 << 24) - 1)
        instance.NCRISC_INIT_ENABLE_BLOB_DONE_IRQ = (value >> 0) & ((1 << 1) - 1)
        instance.NCRISC_INIT_DISABLE_BLOB_DONE_IRQ = (value >> 1) & ((1 << 1) - 1)
        return instance


class Noc_STREAM_SCRATCH_2:
    DRAM_FIFO_RD_PTR_WORDS_HI: int
    DRAM_FIFO_WR_PTR_WORDS_LO: int
    NCRISC_TOTAL_LOOP_ITER: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_SCRATCH_2":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.DRAM_FIFO_RD_PTR_WORDS_HI = (value >> 0) & ((1 << 4) - 1)
        instance.DRAM_FIFO_WR_PTR_WORDS_LO = (value >> 4) & ((1 << 20) - 1)
        instance.NCRISC_TOTAL_LOOP_ITER = (value >> 0) & ((1 << 24) - 1)
        return instance


class Noc_STREAM_SCRATCH_3:
    DRAM_FIFO_WR_PTR_WORDS_HI: int
    DRAM_FIFO_CAPACITY_PTR_WORDS_LO: int
    NCRISC_LOOP_INCR: int
    NCRISC_LOOP_BACK_NUM_CFG_REG_WRITES: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_SCRATCH_3":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.DRAM_FIFO_WR_PTR_WORDS_HI = (value >> 0) & ((1 << 8) - 1)
        instance.DRAM_FIFO_CAPACITY_PTR_WORDS_LO = (value >> 8) & ((1 << 16) - 1)
        instance.NCRISC_LOOP_INCR = (value >> 0) & ((1 << 16) - 1)
        instance.NCRISC_LOOP_BACK_NUM_CFG_REG_WRITES = (value >> 16) & ((1 << 8) - 1)
        return instance


class Noc_STREAM_SCRATCH_4:
    DRAM_FIFO_CAPACITY_PTR_WORDS_HI: int
    DRAM_FIFO_BASE_ADDR_WORDS_LO: int
    NCRISC_LOOP_BACK_AUTO_CFG_PTR: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_SCRATCH_4":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.DRAM_FIFO_CAPACITY_PTR_WORDS_HI = (value >> 0) & ((1 << 12) - 1)
        instance.DRAM_FIFO_BASE_ADDR_WORDS_LO = (value >> 12) & ((1 << 12) - 1)
        instance.NCRISC_LOOP_BACK_AUTO_CFG_PTR = (value >> 0) & ((1 << 24) - 1)
        return instance


class Noc_STREAM_SCRATCH_5:
    DRAM_FIFO_BASE_ADDR_WORDS_HI: int
    DRAM_EN_BLOCKING: int
    """
    Processes the read or write operation to completeion without processing other dram streams in the meantime
    """

    DRAM_DATA_STRUCTURE_IS_LUT: int
    """
    Fifo structure in dram holds a dram pointer and size that is used as indirection to a tile in dram
    """

    DRAM_RESET_RD_PTR_TO_BASE_ON_EMPTY: int
    """
    During a dram read, if its detected that the fifo is empty the ncrisc will reset the read pointer back to base
    Its expected that there is no host interaction
    """

    DRAM_RESET_WR_PTR_TO_BASE_ON_FULL: int
    """
    During a dram write, if its detected that the fifo is full the ncrisc will reset the write pointer back to base. Old data will be overwritten.
    Its expected that there is no host interaction
    """

    DRAM_NO_PTR_UPDATE_ON_PHASE_END: int
    """
    The internal ncrisc rd/wr pointers will not be updated at phase end
    Its expected that there is no host interaction
    """

    DRAM_WR_BUFFER_FLUSH_AND_RST_PTRS: int
    """
    Before ending the phase the ncrisc will wait until the host has emptied the write buffer and then reset the read and write pointers to base
    This can be used for hosts that do not want to track wrapping
    The host must be aware of this behaviour for this functionality to work
    """

    NCRISC_LOOP_NEXT_PIC_INT_ON_PHASE: int

    @classmethod
    def from_buffer_copy(cls, buffer: memoryview) -> "Noc_STREAM_SCRATCH_5":
        instance = cls()
        value = unpack_int(buffer[0:4])
        instance.DRAM_FIFO_BASE_ADDR_WORDS_HI = (value >> 0) & ((1 << 16) - 1)
        instance.DRAM_EN_BLOCKING = (value >> 16) & ((1 << 1) - 1)
        instance.DRAM_DATA_STRUCTURE_IS_LUT = (value >> 17) & ((1 << 1) - 1)
        instance.DRAM_RESET_RD_PTR_TO_BASE_ON_EMPTY = (value >> 18) & ((1 << 1) - 1)
        instance.DRAM_RESET_WR_PTR_TO_BASE_ON_FULL = (value >> 19) & ((1 << 1) - 1)
        instance.DRAM_NO_PTR_UPDATE_ON_PHASE_END = (value >> 20) & ((1 << 1) - 1)
        instance.DRAM_WR_BUFFER_FLUSH_AND_RST_PTRS = (value >> 21) & ((1 << 1) - 1)
        instance.NCRISC_LOOP_NEXT_PIC_INT_ON_PHASE = (value >> 0) & ((1 << 20) - 1)
        return instance


class NocOverlayRegistersState:
    def __init__(self, buffer: bytes):
        self.__buffer = memoryview(buffer)

    @cached_property
    def STREAM_REMOTE_SRC(self) -> Noc_STREAM_REMOTE_SRC:
        """
        Properties of the remote source stream (coorindates, stream ID, and this streams destination index).
        Dont-care unless REMOTE_SOURCE == 1.
        """
        return Noc_STREAM_REMOTE_SRC.from_buffer_copy(self.__buffer[0:])

    @cached_property
    def STREAM_REMOTE_SRC_X(self) -> int:
        return self.STREAM_REMOTE_SRC.STREAM_REMOTE_SRC_X

    @cached_property
    def STREAM_REMOTE_SRC_Y(self) -> int:
        return self.STREAM_REMOTE_SRC.STREAM_REMOTE_SRC_Y

    @cached_property
    def REMOTE_SRC_STREAM_ID(self) -> int:
        return self.STREAM_REMOTE_SRC.REMOTE_SRC_STREAM_ID

    @cached_property
    def STREAM_REMOTE_SRC_DEST_INDEX(self) -> int:
        return self.STREAM_REMOTE_SRC.STREAM_REMOTE_SRC_DEST_INDEX

    @cached_property
    def DRAM_READS__TRANS_SIZE_WORDS_LO(self) -> int:
        return self.STREAM_REMOTE_SRC.DRAM_READS__TRANS_SIZE_WORDS_LO

    @cached_property
    def STREAM_REMOTE_SRC_PHASE(self) -> Noc_STREAM_REMOTE_SRC_PHASE:
        """
        Remote source phase (may be different from the destination stream phase.)
        We use 20-bit phase ID, so phase count doesnt wrap until 1M phases.
        Dont-care unless REMOTE_SOURCE == 1.
        """
        return Noc_STREAM_REMOTE_SRC_PHASE.from_buffer_copy(self.__buffer[4:])

    @cached_property
    def DRAM_READS__SCRATCH_1_PTR(self) -> int:
        return self.STREAM_REMOTE_SRC_PHASE.DRAM_READS__SCRATCH_1_PTR

    @cached_property
    def DRAM_READS__TRANS_SIZE_WORDS_HI(self) -> int:
        return self.STREAM_REMOTE_SRC_PHASE.DRAM_READS__TRANS_SIZE_WORDS_HI

    @cached_property
    def STREAM_REMOTE_DEST(self) -> Noc_STREAM_REMOTE_DEST:
        """
        Properties of the remote destination stream (coorindates, stream ID).  Dont-care unless REMOTE_RECEIVER == 1.
        If destination is multicast, this register specifies the starting coordinates of the destination
        multicast group/rectangle. (The end coordinates are in STREAM_MCAST_DEST below.)
        """
        return Noc_STREAM_REMOTE_DEST.from_buffer_copy(self.__buffer[8:])

    @cached_property
    def STREAM_REMOTE_DEST_X(self) -> int:
        return self.STREAM_REMOTE_DEST.STREAM_REMOTE_DEST_X

    @cached_property
    def STREAM_REMOTE_DEST_Y(self) -> int:
        return self.STREAM_REMOTE_DEST.STREAM_REMOTE_DEST_Y

    @cached_property
    def STREAM_REMOTE_DEST_STREAM_ID(self) -> int:
        return self.STREAM_REMOTE_DEST.STREAM_REMOTE_DEST_STREAM_ID

    @cached_property
    def STREAM_LOCAL_DEST(self) -> Noc_STREAM_LOCAL_DEST:
        """
        Properties of the local destination gather stream connection.
        Dont-care unless LOCAL_RECEIVER == 1.
        Shares register space with STREAM_REMOTE_DEST_REG_INDEX.
        """
        return Noc_STREAM_LOCAL_DEST.from_buffer_copy(self.__buffer[8:])

    @cached_property
    def STREAM_LOCAL_DEST_MSG_CLEAR_NUM(self) -> int:
        return self.STREAM_LOCAL_DEST.STREAM_LOCAL_DEST_MSG_CLEAR_NUM

    @cached_property
    def STREAM_LOCAL_DEST_STREAM_ID(self) -> int:
        return self.STREAM_LOCAL_DEST.STREAM_LOCAL_DEST_STREAM_ID

    @cached_property
    def STREAM_REMOTE_DEST_BUF_START(self) -> Noc_STREAM_REMOTE_DEST_BUF_START:
        """
        Start address (in words) of the remote destination stream memory buffer.
        """
        return Noc_STREAM_REMOTE_DEST_BUF_START.from_buffer_copy(self.__buffer[12:])

    @cached_property
    def DRAM_WRITES__SCRATCH_1_PTR_LO(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_START.DRAM_WRITES__SCRATCH_1_PTR_LO

    @cached_property
    def STREAM_REMOTE_DEST_BUF_SIZE(self) -> Noc_STREAM_REMOTE_DEST_BUF_SIZE:
        """
        Size (in words) of the remote destination stream memory buffer.
        """
        return Noc_STREAM_REMOTE_DEST_BUF_SIZE.from_buffer_copy(self.__buffer[16:])

    @cached_property
    def REMOTE_DEST_BUF_SIZE_WORDS(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_SIZE.REMOTE_DEST_BUF_SIZE_WORDS

    @cached_property
    def DRAM_WRITES__SCRATCH_1_PTR_HI(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_SIZE.DRAM_WRITES__SCRATCH_1_PTR_HI

    @cached_property
    def STREAM_REMOTE_DEST_WR_PTR(self) -> int:
        """
        Write pointer for the remote destination stream memory buffer.
        Can be written directly; automatically reset to 0 when
        STREAM_REMOTE_DEST_BUF_START is written.
        """
        return unpack_int(self.__buffer[20:])

    @cached_property
    def STREAM_BUF_START(self) -> int:
        """
        Start address (in words) of the memory buffer associated with this stream.
        """
        return unpack_int(self.__buffer[24:])

    @cached_property
    def STREAM_BUF_SIZE(self) -> int:
        """
        Stream buffer size (in words).
        """
        return unpack_int(self.__buffer[28:])

    @cached_property
    def STREAM_MSG_INFO_PTR(self) -> int:
        """
        Stream message info buffer address.

        This register needs to be initialized to the start of the message info buffer during
        phase configuration.  Subsequently it will be incremented by hardware as data are read
        from the buffer, thus doubling as the read pointer during phase execution.

        Stream hardware will assume that this buffer is large enough to hold info for all messages
        within a phase, so unlike the buffer, it never needs to wrap.

        The buffer is filled automatically by snooping for streams with remote source.
        For source enpoints, the buffer is written explicitly (along with the data buffer), after which
        STREAM_NUM_MSGS_RECEIVED_INC is written to notify the stream that messages are available for
        sending.

        Write pointer is also managed automatically by hardware, but can be read or reset using
        STREAM_MSG_INFO_WR_PTR_REG. Write pointer is also reset when writing this register.
        """
        return unpack_int(self.__buffer[32:])

    @cached_property
    def STREAM_REMOTE_DEST_MSG_INFO_WR_PTR(self) -> int:
        """
        Write pointer for the remote destination message info buffer.
        Dont-care unless REMOTE_RECEIVER==1.
        Needs to be initialized to the start of the message info buffer of the remote destination
        at phase start, if destination is changed.
        Subsequently its incremented automatically as messages are forwarded.
        """
        return unpack_int(self.__buffer[36:])

    @cached_property
    def STREAM_MISC_CFG(self) -> Noc_STREAM_MISC_CFG:
        """
        The ID of NOCs used for incoming and outgoing data, followed by misc. stream configuration options:
          * Source - set exactly one of these to 1:
               SOURCE_ENDPOINT = source is local math/packer
               REMOTE_SOURCE = source is remote sender stream
               LOCAL_SOURCES_CONNECTED = source is one or more local connected streams
          * Destination - set one or zero of these to 1:
               RECEIVER_ENDPOINT = stream is read by local unpacker/math
               REMOTE_RECEIVER = stream forwards data to a remote destination or multicast group
               LOCAL_RECEIVER = stream is connected to a local destination stream
               None set = stream just stores data in a local buffer, without forwarding/clearing, and
                          finishes the phase once all messages have been received
          * Phase/data forward options:
             PHASE_AUTO_CONFIG = set to 1 for stream to fetch next phase configuration automatically.
             PHASE_AUTO_ADVANCE = set to 1 for stream to advance to next phase automatically
                   (otherwise need to write STREAM_PHASE_ADVANCE below)
             DATA_AUTO_SEND = set to 1 to forward data automatically based on read/write pointers;
                    set to 0 to forward data only when STREAM_NEXT_MSG_SEND is written
        """
        return Noc_STREAM_MISC_CFG.from_buffer_copy(self.__buffer[40:])

    @cached_property
    def INCOMING_DATA_NOC(self) -> int:
        return self.STREAM_MISC_CFG.INCOMING_DATA_NOC

    @cached_property
    def OUTGOING_DATA_NOC(self) -> int:
        return self.STREAM_MISC_CFG.OUTGOING_DATA_NOC

    @cached_property
    def REMOTE_SRC_UPDATE_NOC(self) -> int:
        return self.STREAM_MISC_CFG.REMOTE_SRC_UPDATE_NOC

    @cached_property
    def LOCAL_SOURCES_CONNECTED(self) -> int:
        return self.STREAM_MISC_CFG.LOCAL_SOURCES_CONNECTED

    @cached_property
    def SOURCE_ENDPOINT(self) -> int:
        return self.STREAM_MISC_CFG.SOURCE_ENDPOINT

    @cached_property
    def REMOTE_SOURCE(self) -> int:
        return self.STREAM_MISC_CFG.REMOTE_SOURCE

    @cached_property
    def RECEIVER_ENDPOINT(self) -> int:
        return self.STREAM_MISC_CFG.RECEIVER_ENDPOINT

    @cached_property
    def LOCAL_RECEIVER(self) -> int:
        return self.STREAM_MISC_CFG.LOCAL_RECEIVER

    @cached_property
    def REMOTE_RECEIVER(self) -> int:
        return self.STREAM_MISC_CFG.REMOTE_RECEIVER

    @cached_property
    def PHASE_AUTO_CONFIG(self) -> int:
        return self.STREAM_MISC_CFG.PHASE_AUTO_CONFIG

    @cached_property
    def PHASE_AUTO_ADVANCE(self) -> int:
        return self.STREAM_MISC_CFG.PHASE_AUTO_ADVANCE

    @cached_property
    def DATA_AUTO_SEND(self) -> int:
        return self.STREAM_MISC_CFG.DATA_AUTO_SEND

    @cached_property
    def NEXT_PHASE_SRC_CHANGE(self) -> int:
        return self.STREAM_MISC_CFG.NEXT_PHASE_SRC_CHANGE

    @cached_property
    def NEXT_PHASE_DEST_CHANGE(self) -> int:
        return self.STREAM_MISC_CFG.NEXT_PHASE_DEST_CHANGE

    @cached_property
    def DATA_BUF_NO_FLOW_CTRL(self) -> int:
        """
        set if REMOTE_SOURCE==1 and the buffer is large enough to accept full phase data without wrapping:
        """
        return self.STREAM_MISC_CFG.DATA_BUF_NO_FLOW_CTRL

    @cached_property
    def DEST_DATA_BUF_NO_FLOW_CTRL(self) -> int:
        """
        set if REMOTE_RECEIVER==1 and the destination buffer is large enough to accept full phase data without wrapping:
        """
        return self.STREAM_MISC_CFG.DEST_DATA_BUF_NO_FLOW_CTRL

    @cached_property
    def REMOTE_SRC_IS_MCAST(self) -> int:
        """
        set if REMOTE_SOURCE==1 and has mulicast enabled (i.e. this stream is part of a multicast group)
        """
        return self.STREAM_MISC_CFG.REMOTE_SRC_IS_MCAST

    @cached_property
    def NO_PREV_PHASE_OUTGOING_DATA_FLUSH(self) -> int:
        """
        set if no need to flush outgoing remote data from previous phase
        """
        return self.STREAM_MISC_CFG.NO_PREV_PHASE_OUTGOING_DATA_FLUSH

    @cached_property
    def UNICAST_VC_REG(self) -> int:
        """
        set to one of the values (0-5) to select which VC unicast requests will be sent on
        """
        return self.STREAM_MISC_CFG.UNICAST_VC_REG

    @cached_property
    def REG_UPDATE_VC_REG(self) -> int:
        """
        set to one of the values (0-5) to select which VC control flow updates will be sent on
        """
        return self.STREAM_MISC_CFG.REG_UPDATE_VC_REG

    @cached_property
    def STREAM_CURR_PHASE(self) -> int:
        """
        Current phase number executed by the stream.
        """
        return unpack_int(self.__buffer[44:])

    @cached_property
    def STREAM_PHASE_AUTO_CFG_PTR(self) -> int:
        """
        Pointer to the stream auto-config data. Initialized to the start of
        the auto-config structure at workload start, automatically updated
        subsequenty.
        Specified as byte address, needs to be multiple of 4B.
        """
        return unpack_int(self.__buffer[48:])

    @cached_property
    def STREAM_MCAST_DEST(self) -> Noc_STREAM_MCAST_DEST:
        """
        Destination spec for multicasting streams. STREAM_MCAST_END_X/Y are
        the end coordinate for the multicast rectangle, with the ones from
        STREAM_REMOTE_DEST taken as start.
        Dont-care if STREAM_MCAST_EN == 0.
        """
        return Noc_STREAM_MCAST_DEST.from_buffer_copy(self.__buffer[52:])

    @cached_property
    def STREAM_MCAST_END_X(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_END_X

    @cached_property
    def STREAM_MCAST_END_Y(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_END_Y

    @cached_property
    def STREAM_MCAST_EN(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_EN

    @cached_property
    def STREAM_MCAST_LINKED(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_LINKED

    @cached_property
    def STREAM_MCAST_VC(self) -> int:
        """
        Set to 0 to select VC 4, and 1 to select VC 5 (default 0)
        """
        return self.STREAM_MCAST_DEST.STREAM_MCAST_VC

    @cached_property
    def STREAM_MCAST_NO_PATH_RES(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_NO_PATH_RES

    @cached_property
    def STREAM_MCAST_XY(self) -> int:
        return self.STREAM_MCAST_DEST.STREAM_MCAST_XY

    @cached_property
    def STREAM_MCAST_DEST_NUM(self) -> int:
        """
        Number of multicast destinations (dont-care for non-multicast streams)
        """
        return unpack_int(self.__buffer[56:])

    @cached_property
    def STREAM_GATHER(self) -> Noc_STREAM_GATHER:
        """
        Specifies MSG_ARB_GROUP_SIZE. Valid values are 1 (round-robin
        arbitration between each incoming stream) or 4 (round-robin arbitration
        between groups of 4 incoming streams).
        """
        return Noc_STREAM_GATHER.from_buffer_copy(self.__buffer[60:])

    @cached_property
    def MSG_ARB_GROUP_SIZE(self) -> int:
        return self.STREAM_GATHER.MSG_ARB_GROUP_SIZE

    @cached_property
    def MSG_SRC_IN_ORDER_FWD(self) -> int:
        return self.STREAM_GATHER.MSG_SRC_IN_ORDER_FWD

    @cached_property
    def STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS(self) -> int:
        """
        When using in-order message forwarding, number of messages after which the source
        pointer goes back to zero (without phase change).
        Dont-care if STREAM_MCAST_EN == 0 or MSG_SRC_IN_ORDER_FWD == 0.
        """
        return unpack_int(self.__buffer[64:])

    @cached_property
    def STREAM_MSG_HEADER_FORMAT(self) -> Noc_STREAM_MSG_HEADER_FORMAT:
        """
        Offset & size of the size field in the message header. Only valid offsets are multiples of 8
        (i.e. byte-aligned).
        """
        return Noc_STREAM_MSG_HEADER_FORMAT.from_buffer_copy(self.__buffer[68:])

    @cached_property
    def MSG_HEADER_WORD_CNT_OFFSET(self) -> int:
        return self.STREAM_MSG_HEADER_FORMAT.MSG_HEADER_WORD_CNT_OFFSET

    @cached_property
    def MSG_HEADER_WORD_CNT_BITS(self) -> int:
        return self.STREAM_MSG_HEADER_FORMAT.MSG_HEADER_WORD_CNT_BITS

    @cached_property
    def STREAM_NUM_MSGS_RECEIVED(self) -> int:
        """
        Number of received & stored messages (read-only).
        To get the total number of messages penidng in memory read
        STREAM_NUM_MSGS_RECEIVED_IN_BUF_AND_MEM_REG_INDEX
        """
        return unpack_int(self.__buffer[72:])

    @cached_property
    def STREAM_NEXT_RECEIVED_MSG_ADDR(self) -> int:
        """
        Memory address (in words) of the next in line received message (read-only).
        """
        return unpack_int(self.__buffer[76:])

    @cached_property
    def STREAM_NEXT_RECEIVED_MSG_SIZE(self) -> int:
        """
        Size in words of the next in line received message (read-only).
        """
        return unpack_int(self.__buffer[80:])

    @cached_property
    def STREAM_MSG_INFO_CLEAR(self) -> int:
        """
        Clear message info for one or more stored messages.  Only valid values are 1, 2, or 4.
        No effect on the read pointer.
        Should be used only for streams where RECEIVER_ENDPOINT == 1.
        """
        return unpack_int(self.__buffer[84:])

    @cached_property
    def STREAM_MSG_DATA_CLEAR(self) -> int:
        """
        Move read pointer & reclaim buffer space for one or more stored messages.
        Sends flow control update to the source if REMOTE_SOURCE==1.
        Only valid values are 1, 2, or 4.
        Should be used only for streams where RECEIVER_ENDPOINT == 1, after
        STREAM_MSG_INFO_CLEAR_REG has been written with the same value.
        """
        return unpack_int(self.__buffer[88:])

    @cached_property
    def STREAM_NEXT_MSG_SEND(self) -> int:
        """
        Write to send the next in line stored message. Used when DATA_AUTO_SEND == 0.
        """
        return unpack_int(self.__buffer[92:])

    @cached_property
    def STREAM_RD_PTR(self) -> int:
        """
        Read pointer value (word offset relative to buffer start). Can be updated by
        writing the register (e.g. to force resend).
        Value does not guarantee that all data up to the current value have been sent
        off (forwarding command may be  ongoing).  To find out free space in the buffer,
        read STREAM_BUF_SPACE_AVAILABLE.
        Automatically reset to 0 when STREAM_BUF_START_REG is updated.
        """
        return unpack_int(self.__buffer[96:])

    @cached_property
    def STREAM_WR_PTR(self) -> int:
        """
        Write pointer value (word offset relative to buffer start).
        Can be read to determine the location at which to write new data.
        In normal operation, should be updated only by writing
        STREAM_NUM_MSGS_RECEIVED_INC_REG or STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG.
        """
        return unpack_int(self.__buffer[100:])

    @cached_property
    def STREAM_MSG_INFO_WR_PTR(self) -> int:
        """
        Write pointer value for message info buffer (absolute word address).
        In normal operation, should be updated only by writing
        STREAM_NUM_MSGS_RECEIVED_INC_REG or STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG.
        """
        return unpack_int(self.__buffer[104:])

    @cached_property
    def STREAM_PHASE_ADVANCE(self) -> int:
        """
        Write-only. Write 1 to advance to the next phase if PHASE_AUTO_ADVANCE == 0.
        """
        return unpack_int(self.__buffer[108:])

    @cached_property
    def STREAM_BUF_SPACE_AVAILABLE(self) -> int:
        """
        Available buffer space at the stream (in 16B words).
        Source cant send data unless available space > 0.
        """
        return unpack_int(self.__buffer[112:])

    @cached_property
    def STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO(self) -> Noc_STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO:
        """
        For endpoints with SOURCE_ENDPOINT == 1, this register is for firmware
        to register new message for sending.
        This updates the msg_info register structure directly, rather than writing to the message info
        buffer in memory.
        Must not be written when the message info register structure is full, or if
        there are message info entries in the memory buffer. (This would cause a race
        condition.)
        """
        return Noc_STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO.from_buffer_copy(self.__buffer[116:])

    @cached_property
    def SOURCE_ENDPOINT_NEW_MSG_ADDR(self) -> int:
        return self.STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO.SOURCE_ENDPOINT_NEW_MSG_ADDR

    @cached_property
    def SOURCE_ENDPOINT_NEW_MSG_SIZE(self) -> int:
        return self.STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO.SOURCE_ENDPOINT_NEW_MSG_SIZE

    @cached_property
    def STREAM_NUM_MSGS_RECEIVED_INC(self) -> Noc_STREAM_NUM_MSGS_RECEIVED_INC:
        """
        For endpoints with SOURCE_ENDPOINT == 1, this register is for firmware
        to update the number of messages whose data & header are available in the memory buffer.
        Hardware register is incremented atomically if sending of previous messages is in progress.
        """
        return Noc_STREAM_NUM_MSGS_RECEIVED_INC.from_buffer_copy(self.__buffer[120:])

    @cached_property
    def SOURCE_ENDPOINT_NEW_MSGS_NUM(self) -> int:
        return self.STREAM_NUM_MSGS_RECEIVED_INC.SOURCE_ENDPOINT_NEW_MSGS_NUM

    @cached_property
    def SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE(self) -> int:
        return self.STREAM_NUM_MSGS_RECEIVED_INC.SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE

    @cached_property
    def STREAM_RESET(self) -> int:
        """
        Write to reset & stop stream.
        """
        return unpack_int(self.__buffer[124:])

    @cached_property
    def STREAM_DEST_PHASE_READY_UPDATE(self) -> Noc_STREAM_DEST_PHASE_READY_UPDATE:
        """
        Write phase number to indicate destination ready for the given phase.
        (This is done automatically by stream hardware when starting a phase with REMOTE_SOURCE=1.)
        The phase number is the one indicated by STREAM_REMOTE_SRC_PHASE_REG at destination.
        This register is mapped to the shared destination ready table, not a per-stream register.
        (Stream index is taken from the register address, and stored into the table along with the
        phase number.)
        """
        return Noc_STREAM_DEST_PHASE_READY_UPDATE.from_buffer_copy(self.__buffer[128:])

    @cached_property
    def PHASE_READY_DEST_NUM(self) -> int:
        return self.STREAM_DEST_PHASE_READY_UPDATE.PHASE_READY_DEST_NUM

    @cached_property
    def PHASE_READY_NUM(self) -> int:
        return self.STREAM_DEST_PHASE_READY_UPDATE.PHASE_READY_NUM

    @cached_property
    def PHASE_READY_MCAST(self) -> int:
        """
        set if this stream is part of multicast group (i.e. if REMOTE_SRC_IS_MCAST==1)
        """
        return self.STREAM_DEST_PHASE_READY_UPDATE.PHASE_READY_MCAST

    @cached_property
    def PHASE_READY_TWO_WAY_RESP(self) -> int:
        """
        set if the message is in response to 2-way handshake
        """
        return self.STREAM_DEST_PHASE_READY_UPDATE.PHASE_READY_TWO_WAY_RESP

    @cached_property
    def STREAM_SRC_READY_UPDATE(self) -> Noc_STREAM_SRC_READY_UPDATE:
        """
        Source ready message register for two-way handshake (sent by source in
        case destination ready entry is not found in the table).
        If received by a stream that already sent its ready update, it prompts resending.
        """
        return Noc_STREAM_SRC_READY_UPDATE.from_buffer_copy(self.__buffer[132:])

    @cached_property
    def STREAM_REMOTE_RDY_SRC_X(self) -> int:
        return self.STREAM_SRC_READY_UPDATE.STREAM_REMOTE_RDY_SRC_X

    @cached_property
    def STREAM_REMOTE_RDY_SRC_Y(self) -> int:
        return self.STREAM_SRC_READY_UPDATE.STREAM_REMOTE_RDY_SRC_Y

    @cached_property
    def REMOTE_RDY_SRC_STREAM_ID(self) -> int:
        return self.STREAM_SRC_READY_UPDATE.REMOTE_RDY_SRC_STREAM_ID

    @cached_property
    def STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE(self) -> Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE:
        """
        Update available buffer space at remote destination stream.
        this is rd_ptr increment issued when a message is forwarded
        """
        return Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE.from_buffer_copy(self.__buffer[136:])

    @cached_property
    def REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_DEST_NUM(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE.REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_DEST_NUM

    @cached_property
    def REMOTE_DEST_BUF_WORDS_FREE_INC(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE.REMOTE_DEST_BUF_WORDS_FREE_INC

    @cached_property
    def STREAM_WAIT_STATUS(self) -> Noc_STREAM_WAIT_STATUS:
        """
        Status info for the stream.
        """
        return Noc_STREAM_WAIT_STATUS.from_buffer_copy(self.__buffer[140:])

    @cached_property
    def WAIT_SW_PHASE_ADVANCE_SIGNAL(self) -> int:
        """
        Set when stream is in START state with auto-config disabled, or if auto-config is enabled
        but PHASE_AUTO_ADVANCE=0
        """
        return self.STREAM_WAIT_STATUS.WAIT_SW_PHASE_ADVANCE_SIGNAL

    @cached_property
    def WAIT_PREV_PHASE_DATA_FLUSH(self) -> int:
        """
        Set when stream has configured the current phase, but waits data from the previous one to be flushed.
        """
        return self.STREAM_WAIT_STATUS.WAIT_PREV_PHASE_DATA_FLUSH

    @cached_property
    def MSG_FWD_ONGOING(self) -> int:
        """
        Set when stream is in data forwarding state.
        """
        return self.STREAM_WAIT_STATUS.MSG_FWD_ONGOING

    @cached_property
    def STREAM_CURR_STATE(self) -> int:
        return self.STREAM_WAIT_STATUS.STREAM_CURR_STATE

    @cached_property
    def STREAM_PHASE_AUTO_CFG_HEADER(self) -> Noc_STREAM_PHASE_AUTO_CFG_HEADER:
        """
        Register corresponding to the auto-configuration header. Written by each auto-config access
        at phase start, can be also written by software for initial configuration or if auto-config
        is disabled.
        PHASE_NUM_INCR is phase number increment relative to the previous executed phase (or 0 right
        after reset). The increment happens after auto-config is done, and before the phase is executed.
        (Therefore reading  STREAM_CURR_PHASE_REG while auto-config is ongoing, or if it hasnt started
        yet, may return the old phase number.)
        This enables up to 2^12-1 phases to be skipped. If more phases need to be skipped, it is
        necessary to insert an intermediate phase with zero messages, whose only purpose is to provide
        an additional skip offset.
        """
        return Noc_STREAM_PHASE_AUTO_CFG_HEADER.from_buffer_copy(self.__buffer[144:])

    @cached_property
    def PHASE_NUM_INCR(self) -> int:
        return self.STREAM_PHASE_AUTO_CFG_HEADER.PHASE_NUM_INCR

    @cached_property
    def CURR_PHASE_NUM_MSGS(self) -> int:
        return self.STREAM_PHASE_AUTO_CFG_HEADER.CURR_PHASE_NUM_MSGS

    @cached_property
    def NEXT_PHASE_NUM_CFG_REG_WRITES(self) -> int:
        return self.STREAM_PHASE_AUTO_CFG_HEADER.NEXT_PHASE_NUM_CFG_REG_WRITES

    @cached_property
    def STREAM_PERF_CONFIG(self) -> Noc_STREAM_PERF_CONFIG:
        """
        Should be written only for stream 0, applies to all streams.
        """
        return Noc_STREAM_PERF_CONFIG.from_buffer_copy(self.__buffer[148:])

    @cached_property
    def CLOCK_GATING_EN(self) -> int:
        return self.STREAM_PERF_CONFIG.CLOCK_GATING_EN

    @cached_property
    def CLOCK_GATING_HYST(self) -> int:
        return self.STREAM_PERF_CONFIG.CLOCK_GATING_HYST

    @cached_property
    def PARTIAL_SEND_WORDS_THR(self) -> int:
        """
        PARTIAL_SEND_WORDS_THR contols the minimum number of 16-byte words of a tile to accumulate in a relay stream before sending it off to the destination.
        If the size of the tile is less than or equal to PARTIAL_SEND_WORDS_THR, then this feild is ignored.
        Default is 16 words
        """
        return self.STREAM_PERF_CONFIG.PARTIAL_SEND_WORDS_THR

    @cached_property
    def STREAM_MSG_GROUP_ZERO_MASK_AND(self) -> int:
        """
        AND value of zero masks for the pending message group.
        (Header bits [95:64].)
        Read-only.  Valid only for receiver endpoint streams.
        """
        return unpack_int(self.__buffer[152:])

    @cached_property
    def STREAM_MSG_INFO_FULL(self) -> int:
        """
        Returns 1 if the message info register is full (read-only).
        """
        return unpack_int(self.__buffer[156:])

    @cached_property
    def STREAM_MEM_BUF_SPACE_AVAILABLE_ACK_THRESHOLD(self) -> int:
        """
        4-bit wide register that determines the threshold at which a stream
        with remote source sends an update message to STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE.
        Dont-care unless REMOTE_SOURCE==1.
        Values:
          value[3:0] == 0 => disable threshold. Acks send as soon as any data are cleared/forwarded.
          value[3:0] >  0 => threshold calculated according to the following formula:
                if (value[3])
                     threshold = buf_size - (buf_size >> value[2:0])
                else
                     threshold = (buf_size >> value[2:0])

        This enables setting thresholds of buf_size/2, buf_size/4, buf_size/8, ... buf_size/256,
        as well as  3*buf_size/4, 7*buf_size/8, etc.
        """
        return unpack_int(self.__buffer[160:])

    @cached_property
    def STREAM_MSG_INFO_CAN_PUSH_NEW_MSG(self) -> int:
        """
        Returns 1 if the message info register can accept new message push (read-only).
        Equivalent to checking the condition:
          (STREAM_MSG_INFO_FULL_REG_INDEX == 0) && (STREAM_MSG_INFO_PTR_REG_INDEX == STREAM_MSG_INFO_WR_PTR_REG_INDEX)
        (I.e. ther is free space in the msg info register, and we dont have any message info headers in the
         memory buffer about to be fetched.)
        """
        return unpack_int(self.__buffer[164:])

    @cached_property
    def STREAM_MSG_GROUP_COMPRESS(self) -> int:
        """
        Concat compress flags from 4 tiles in the pending message group.
        (Header bit 52.)
        Read-only.  Valid only for receiver endpoint streams.
        """
        return unpack_int(self.__buffer[168:])

    @cached_property
    def STREAM_GATHER_CLEAR(self) -> Noc_STREAM_GATHER_CLEAR:
        """
        Msg_LOCAL_STREAM_CLEAR_NUM specifies the number of messages that should
        be cleared from a gather stream before moving onto the next stream.
        When MSG_ARB_GROUP_SIZE > 1, the order of clearing the streams can be selected
        with MSG_GROUP_STREAM_CLEAR_TYPE. 0 = clear the whole group MSG_LOCAL_STREAM_CLEAR_NUM times,
        1 = clear each stream of the group MSG_LOCAL_STREAM_CLEAR_NUM times before
        moving onto the next stream in the group.
        """
        return Noc_STREAM_GATHER_CLEAR.from_buffer_copy(self.__buffer[172:])

    @cached_property
    def MSG_LOCAL_STREAM_CLEAR_NUM(self) -> int:
        return self.STREAM_GATHER_CLEAR.MSG_LOCAL_STREAM_CLEAR_NUM

    @cached_property
    def MSG_GROUP_STREAM_CLEAR_TYPE(self) -> int:
        return self.STREAM_GATHER_CLEAR.MSG_GROUP_STREAM_CLEAR_TYPE

    @cached_property
    def STREAM_REMOTE_DEST_TRAFFIC_PRIORITY(self) -> int:
        """
        Priority for traffic sent to remote destination.
        Valid only for streams capable of remote sending.
        4-bit value.
        Set to 0 to send traffic under round-robin arbitration.
        Set to 1-15 for priority arbitration (higher values are higher priority).
        """
        return unpack_int(self.__buffer[176:])

    @cached_property
    def STREAM_DEBUG_STATUS_SEL(self) -> Noc_STREAM_DEBUG_STATUS_SEL:
        """
        Debug bus stream selection. Write the stream id for the stream that you want exposed on the debug bus
        This register only exists in stream 0.
        """
        return Noc_STREAM_DEBUG_STATUS_SEL.from_buffer_copy(self.__buffer[180:])

    @cached_property
    def DEBUG_STATUS_STREAM_ID_SEL(self) -> int:
        return self.STREAM_DEBUG_STATUS_SEL.DEBUG_STATUS_STREAM_ID_SEL

    @cached_property
    def DISABLE_DEST_READY_TABLE(self) -> int:
        return self.STREAM_DEBUG_STATUS_SEL.DISABLE_DEST_READY_TABLE

    @cached_property
    def STREAM_DEBUG_ASSERTIONS(self) -> int:
        """
        Debugging: Non-zero value indicates an invalid stream operation occured.
        Sticky, write 1 to clear.
        """
        return unpack_int(self.__buffer[184:])

    @cached_property
    def STREAM_NUM_MSGS_RECEIVED_IN_BUF_AND_MEM(self) -> int:
        """
        Only in receiver endpoint streams (stream 4 and 5)
        Read-only. Tells you the number of tiles that have arrived in L1
        """
        return unpack_int(self.__buffer[188:])

    @cached_property
    def STREAM_LOCAL_SRC_MASK(self) -> int:
        """
        Bit mask of connnected local source. Dont care if LOCAL_SOURCES_CONNECTED == 0.
        Mask segments [23:0], [47:24], and [63:48] are at indexes STREAM_LOCAL_SRC_MASK_REG_INDEX,
        STREAM_LOCAL_SRC_MASK_REG_INDEX+1, STREAM_LOCAL_SRC_MASK_REG_INDEX+2.
        """
        return unpack_int(self.__buffer[192:])

    @cached_property
    def STREAM_RECEIVER_ENDPOINT_SET_MSG_HEADER(self) -> int:
        """
        For receiver endpoint streams that expose the full message header bus to unpacker,
        write this register to specify the full header in case the stream is not snooping
        a remote source but instead also works as a source endpoint.
        Write (STREAM_RECEIVER_ENDPOINT_SET_MSG_HEADER_REG_INDEX+i) to set bits [i*32 +: 32]
        of the message header for the next message, prior to writing STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX.
        """
        return unpack_int(self.__buffer[240:])

    @cached_property
    def STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE(self) -> Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE:
        """
        Available buffer space at remote destination stream(s).
        Dont care unless REMOTE_RECEIVER == 1.
        Source cant send data unless WORDS_FREE > 0.
        Read-only; updated automatically to maximum value when
        STREAM_REMOTE_DEST_BUF_SIZE_REG is updated.
        For multicast streams, values for successive destinations are at
        subsequent indexes (STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX+1,
        STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX+2, etc.).
        """
        return Noc_STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE.from_buffer_copy(self.__buffer[256:])

    @cached_property
    def REMOTE_DEST_WORDS_FREE(self) -> int:
        return self.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE.REMOTE_DEST_WORDS_FREE

    @cached_property
    def STREAM_RECEIVER_MSG_INFO(self) -> int:
        """
        Read-only register view of the bits on the o_full_msg_info bus.
        Exposed as 32-bit read-only registers starting at this index.
        """
        return unpack_int(self.__buffer[512:])

    @cached_property
    def STREAM_DEBUG_STATUS(self) -> int:
        """
        Read-only register that exposes internal states of the stream.
        Useful for debugging. Valid 32-bit data from STREAM_DEBUG_STATUS_REG_INDEX + 0 to STREAM_DEBUG_STATUS_REG_INDEX + 9
        """
        return unpack_int(self.__buffer[896:])

    @cached_property
    def STREAM_BLOB_AUTO_CFG_DONE(self) -> int:
        """
        32 bit register. Each bit denotes whether the corresponding stream has completed its blob run and is in idle state.
        Resets to 0 upon starting a new stream run. Initially all are 0 to exclude streams that might not be used.
        Can be manually reset to 0 by writing 1 to the corresponding bit.
        Exists only in stream 0
        """
        return unpack_int(self.__buffer[936:])

    @cached_property
    def STREAM_REMOTE_DEST_BUF_START_HI(self) -> int:
        """
        High bits for STREAM_REMOTE_DEST_BUF_START
        """
        return unpack_int(self.__buffer[968:])

    @cached_property
    def STREAM_REMOTE_DEST_MSG_INFO_WR_PTR_HI(self) -> int:
        """
        High bits for STREAM_REMOTE_DEST_MSG_INFO_WR_PTR
        """
        return unpack_int(self.__buffer[972:])

    @cached_property
    def STREAM_CURR_PHASE_BASE(self) -> int:
        """
        Actual phase number executed is STREAM_CURR_PHASE_BASE_REG_INDEX + STREAM_CURR_PHASE_REG_INDEX
        When reprogramming this register you must also reprogram STREAM_CURR_PHASE_REG_INDEX and STREAM_REMOTE_SRC_PHASE_REG_INDEX
        """
        return unpack_int(self.__buffer[976:])

    @cached_property
    def STREAM_PHASE_AUTO_CFG_PTR_BASE(self) -> int:
        """
        Actual address accessed will be STREAM_PHASE_AUTO_CFG_PTR_BASE_REG_INDEX + STREAM_PHASE_AUTO_CFG_PTR_REG_INDEX
        When reprogramming this register you must also reprogram STREAM_PHASE_AUTO_CFG_PTR_REG_INDEX
        """
        return unpack_int(self.__buffer[980:])

    @cached_property
    def STREAM_BLOB_NEXT_AUTO_CFG_DONE(self) -> Noc_STREAM_BLOB_NEXT_AUTO_CFG_DONE:
        """
        Reading this register will give you a stream id of a stream that finished its blob (according to STREAM_BLOB_AUTO_CFG_DONE_REG_INDEX)
        Subsequent reads will give you the next stream, untill all streams are read, after which it will loop
        This register is only valid if BLOB_NEXT_AUTO_CFG_DONE_VALID is set (i.e. if STREAM_BLOB_AUTO_CFG_DONE_REG_INDEX non-zero)
        Exists only in stream 0
        """
        return Noc_STREAM_BLOB_NEXT_AUTO_CFG_DONE.from_buffer_copy(self.__buffer[984:])

    @cached_property
    def BLOB_NEXT_AUTO_CFG_DONE_STREAM_ID(self) -> int:
        return self.STREAM_BLOB_NEXT_AUTO_CFG_DONE.BLOB_NEXT_AUTO_CFG_DONE_STREAM_ID

    @cached_property
    def BLOB_NEXT_AUTO_CFG_DONE_VALID(self) -> int:
        return self.STREAM_BLOB_NEXT_AUTO_CFG_DONE.BLOB_NEXT_AUTO_CFG_DONE_VALID

    @cached_property
    def FIRMWARE_SCRATCH(self) -> int:
        """
        Scratch location for firmware usage
        Guarantees that no side-effects occur in Overlay hardware
        """
        return unpack_int(self.__buffer[988:])

    @cached_property
    def STREAM_SCRATCH(self) -> int:
        """
        Scratch registers
        Exists only in streams 0-3 and 8-11
        Data can be stored at [23:0] from STREAM_SCRATCH_REG_INDEX + 0 to STREAM_SCRATCH_REG_INDEX + 5
        Can be loaded through overlay blobs.
        """
        return unpack_int(self.__buffer[992:])

    @cached_property
    def STREAM_SCRATCH_0(self) -> Noc_STREAM_SCRATCH_0:
        return Noc_STREAM_SCRATCH_0.from_buffer_copy(self.__buffer[992:])

    @cached_property
    def NCRISC_TRANS_EN(self) -> int:
        return self.STREAM_SCRATCH_0.NCRISC_TRANS_EN

    @cached_property
    def NCRISC_TRANS_EN_IRQ_ON_BLOB_END(self) -> int:
        return self.STREAM_SCRATCH_0.NCRISC_TRANS_EN_IRQ_ON_BLOB_END

    @cached_property
    def NCRISC_CMD_ID(self) -> int:
        return self.STREAM_SCRATCH_0.NCRISC_CMD_ID

    @cached_property
    def NEXT_NRISC_PIC_INT_ON_PHASE(self) -> int:
        """
        Kept for compatibility with grayskull, but doesnt not exist anymore in wormhole
        """
        return self.STREAM_SCRATCH_0.NEXT_NRISC_PIC_INT_ON_PHASE

    @cached_property
    def STREAM_SCRATCH_1(self) -> Noc_STREAM_SCRATCH_1:
        return Noc_STREAM_SCRATCH_1.from_buffer_copy(self.__buffer[996:])

    @cached_property
    def DRAM_FIFO_RD_PTR_WORDS_LO(self) -> int:
        return self.STREAM_SCRATCH_1.DRAM_FIFO_RD_PTR_WORDS_LO

    @cached_property
    def NCRISC_LOOP_COUNT(self) -> int:
        return self.STREAM_SCRATCH_1.NCRISC_LOOP_COUNT

    @cached_property
    def NCRISC_INIT_ENABLE_BLOB_DONE_IRQ(self) -> int:
        return self.STREAM_SCRATCH_1.NCRISC_INIT_ENABLE_BLOB_DONE_IRQ

    @cached_property
    def NCRISC_INIT_DISABLE_BLOB_DONE_IRQ(self) -> int:
        return self.STREAM_SCRATCH_1.NCRISC_INIT_DISABLE_BLOB_DONE_IRQ

    @cached_property
    def STREAM_SCRATCH_2(self) -> Noc_STREAM_SCRATCH_2:
        return Noc_STREAM_SCRATCH_2.from_buffer_copy(self.__buffer[1000:])

    @cached_property
    def DRAM_FIFO_RD_PTR_WORDS_HI(self) -> int:
        return self.STREAM_SCRATCH_2.DRAM_FIFO_RD_PTR_WORDS_HI

    @cached_property
    def DRAM_FIFO_WR_PTR_WORDS_LO(self) -> int:
        return self.STREAM_SCRATCH_2.DRAM_FIFO_WR_PTR_WORDS_LO

    @cached_property
    def NCRISC_TOTAL_LOOP_ITER(self) -> int:
        return self.STREAM_SCRATCH_2.NCRISC_TOTAL_LOOP_ITER

    @cached_property
    def STREAM_SCRATCH_3(self) -> Noc_STREAM_SCRATCH_3:
        return Noc_STREAM_SCRATCH_3.from_buffer_copy(self.__buffer[1004:])

    @cached_property
    def DRAM_FIFO_WR_PTR_WORDS_HI(self) -> int:
        return self.STREAM_SCRATCH_3.DRAM_FIFO_WR_PTR_WORDS_HI

    @cached_property
    def DRAM_FIFO_CAPACITY_PTR_WORDS_LO(self) -> int:
        return self.STREAM_SCRATCH_3.DRAM_FIFO_CAPACITY_PTR_WORDS_LO

    @cached_property
    def NCRISC_LOOP_INCR(self) -> int:
        return self.STREAM_SCRATCH_3.NCRISC_LOOP_INCR

    @cached_property
    def NCRISC_LOOP_BACK_NUM_CFG_REG_WRITES(self) -> int:
        return self.STREAM_SCRATCH_3.NCRISC_LOOP_BACK_NUM_CFG_REG_WRITES

    @cached_property
    def STREAM_SCRATCH_4(self) -> Noc_STREAM_SCRATCH_4:
        return Noc_STREAM_SCRATCH_4.from_buffer_copy(self.__buffer[1008:])

    @cached_property
    def DRAM_FIFO_CAPACITY_PTR_WORDS_HI(self) -> int:
        return self.STREAM_SCRATCH_4.DRAM_FIFO_CAPACITY_PTR_WORDS_HI

    @cached_property
    def DRAM_FIFO_BASE_ADDR_WORDS_LO(self) -> int:
        return self.STREAM_SCRATCH_4.DRAM_FIFO_BASE_ADDR_WORDS_LO

    @cached_property
    def NCRISC_LOOP_BACK_AUTO_CFG_PTR(self) -> int:
        return self.STREAM_SCRATCH_4.NCRISC_LOOP_BACK_AUTO_CFG_PTR

    @cached_property
    def STREAM_SCRATCH_5(self) -> Noc_STREAM_SCRATCH_5:
        return Noc_STREAM_SCRATCH_5.from_buffer_copy(self.__buffer[1012:])

    @cached_property
    def DRAM_FIFO_BASE_ADDR_WORDS_HI(self) -> int:
        return self.STREAM_SCRATCH_5.DRAM_FIFO_BASE_ADDR_WORDS_HI

    @cached_property
    def DRAM_EN_BLOCKING(self) -> int:
        """
        Processes the read or write operation to completeion without processing other dram streams in the meantime
        """
        return self.STREAM_SCRATCH_5.DRAM_EN_BLOCKING

    @cached_property
    def DRAM_DATA_STRUCTURE_IS_LUT(self) -> int:
        """
        Fifo structure in dram holds a dram pointer and size that is used as indirection to a tile in dram
        """
        return self.STREAM_SCRATCH_5.DRAM_DATA_STRUCTURE_IS_LUT

    @cached_property
    def DRAM_RESET_RD_PTR_TO_BASE_ON_EMPTY(self) -> int:
        """
        During a dram read, if its detected that the fifo is empty the ncrisc will reset the read pointer back to base
        Its expected that there is no host interaction
        """
        return self.STREAM_SCRATCH_5.DRAM_RESET_RD_PTR_TO_BASE_ON_EMPTY

    @cached_property
    def DRAM_RESET_WR_PTR_TO_BASE_ON_FULL(self) -> int:
        """
        During a dram write, if its detected that the fifo is full the ncrisc will reset the write pointer back to base. Old data will be overwritten.
        Its expected that there is no host interaction
        """
        return self.STREAM_SCRATCH_5.DRAM_RESET_WR_PTR_TO_BASE_ON_FULL

    @cached_property
    def DRAM_NO_PTR_UPDATE_ON_PHASE_END(self) -> int:
        """
        The internal ncrisc rd/wr pointers will not be updated at phase end
        Its expected that there is no host interaction
        """
        return self.STREAM_SCRATCH_5.DRAM_NO_PTR_UPDATE_ON_PHASE_END

    @cached_property
    def DRAM_WR_BUFFER_FLUSH_AND_RST_PTRS(self) -> int:
        """
        Before ending the phase the ncrisc will wait until the host has emptied the write buffer and then reset the read and write pointers to base
        This can be used for hosts that do not want to track wrapping
        The host must be aware of this behaviour for this functionality to work
        """
        return self.STREAM_SCRATCH_5.DRAM_WR_BUFFER_FLUSH_AND_RST_PTRS

    @cached_property
    def NCRISC_LOOP_NEXT_PIC_INT_ON_PHASE(self) -> int:
        return self.STREAM_SCRATCH_5.NCRISC_LOOP_NEXT_PIC_INT_ON_PHASE

    def get_stream_reg_field(self, reg_index: int, start_bit: int, num_bits: int):
        value = unpack_int(self.__buffer[reg_index * 4 :])
        mask = (1 << num_bits) - 1
        value = (value >> start_bit) & mask
        return value
