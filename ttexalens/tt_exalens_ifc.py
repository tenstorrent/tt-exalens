# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from enum import Enum
import io
import os
import sys
import struct
import zmq

from ttexalens import util as util
from ttexalens import tt_exalens_ifc_cache as tt_exalens_ifc_cache
from ttexalens.tt_exalens_ifc_base import TTExaLensCommunicator


class ttexalens_server_request_type(Enum):
    # Basic requests
    invalid = 0
    ping = 1

    # Device requests
    pci_read32 = 10
    pci_write32 = 11
    pci_read = 12
    pci_write = 13
    pci_read32_raw = 14
    pci_write32_raw = 15
    dma_buffer_read32 = 16
    get_device_ids = 18
    get_device_arch = 19
    get_device_soc_description = 20
    arc_msg = 21

    jtag_read32 = 50
    jtag_write32 = 51
    jtag_read32_axi = 52
    jtag_write32_axi = 53

    # Runtime requests
    pci_read_tile = 100
    get_cluster_description = 102
    convert_from_noc0 = 103

    # File requests
    get_file = 200


class ttexalens_server_bad_request(Exception):
    pass


class ttexalens_server_not_supported(Exception):
    pass


class ttexalens_server_communication:
    """
    This class handles the communication with the TTExaLens server using ZMQ. It is responsible for sending requests and
    parsing and checking the responses.
    """

    _BAD_REQUEST = b"BAD_REQUEST"
    _NOT_SUPPORTED = b"NOT_SUPPORTED"

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(f"tcp://{self.address}:{self.port}")

    def _check(self, response: bytes):
        if response == ttexalens_server_communication._BAD_REQUEST:
            raise ttexalens_server_bad_request()
        if response == ttexalens_server_communication._NOT_SUPPORTED:
            raise ttexalens_server_not_supported()
        return response

    def ping(self):
        self._socket.send(bytes([ttexalens_server_request_type.ping.value]))
        return self._check(self._socket.recv())

    def pci_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        self._socket.send(
            struct.pack(
                "<BBBBBQ",
                ttexalens_server_request_type.pci_read32.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
            )
        )
        return self._check(self._socket.recv())

    def pci_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBBBBQI",
                ttexalens_server_request_type.pci_write32.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())

    def pci_read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        self._socket.send(
            struct.pack(
                "<BBBBBQI",
                ttexalens_server_request_type.pci_read.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
                size,
            )
        )
        return self._check(self._socket.recv())

    def pci_write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        self._socket.send(
            struct.pack(
                f"<BBBBBQI{len(data)}s",
                ttexalens_server_request_type.pci_write.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
                len(data),
                data,
            )
        )
        return self._check(self._socket.recv())

    def pci_read32_raw(self, chip_id: int, address: int):
        self._socket.send(struct.pack("<BBI", ttexalens_server_request_type.pci_read32_raw.value, chip_id, address))
        return self._check(self._socket.recv())

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBII",
                ttexalens_server_request_type.pci_write32_raw.value,
                chip_id,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        self._socket.send(
            struct.pack(
                "<BBQH",
                ttexalens_server_request_type.dma_buffer_read32.value,
                chip_id,
                address,
                channel,
            )
        )
        return self._check(self._socket.recv())

    def pci_read_tile(
        self,
        noc_id: int,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        self._socket.send(
            struct.pack(
                "<BBBBBQIB",
                ttexalens_server_request_type.pci_read_tile.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
                size,
                data_format,
            )
        )
        return self._check(self._socket.recv())

    def get_cluster_description(self):
        self._socket.send(bytes([ttexalens_server_request_type.get_cluster_description.value]))
        return self._check(self._socket.recv())

    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        core_type = core_type.encode()
        coord_system = coord_system.encode()
        data = core_type + coord_system
        self._socket.send(
            struct.pack(
                f"<BBBBII{len(data)}s",
                ttexalens_server_request_type.convert_from_noc0.value,
                chip_id,
                noc_x,
                noc_y,
                len(core_type),
                len(coord_system),
                data,
            )
        )
        bytes = self._check(self._socket.recv())
        if len(bytes) == 2:
            return (bytes[0], bytes[1])
        return bytes

    def get_device_ids(self):
        self._socket.send(bytes([ttexalens_server_request_type.get_device_ids.value]))
        return self._check(self._socket.recv())

    def get_device_arch(self, chip_id: int):
        self._socket.send(
            struct.pack(
                "<BB",
                ttexalens_server_request_type.get_device_arch.value,
                chip_id,
            )
        )
        return self._check(self._socket.recv())

    def get_device_soc_description(self, chip_id: int):
        self._socket.send(
            struct.pack(
                "<BB",
                ttexalens_server_request_type.get_device_soc_description.value,
                chip_id,
            )
        )
        return self._check(self._socket.recv())

    def get_file(self, path: str):
        encoded_path = path.encode()
        self._socket.send(
            struct.pack(
                f"<BI{len(encoded_path)}s",
                ttexalens_server_request_type.get_file.value,
                len(encoded_path),
                encoded_path,
            )
        )
        return self._check(self._socket.recv())

    def arc_msg(
        self, noc_id: int, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
    ):
        self._socket.send(
            struct.pack(
                "<BBBBIIIIB",
                ttexalens_server_request_type.arc_msg.value,
                noc_id,
                device_id,
                msg_code,
                wait_for_done,
                arg0,
                arg1,
                timeout,
            )
        )
        return self._check(self._socket.recv())

    def jtag_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        self._socket.send(
            struct.pack(
                "<BBBBBQ",
                ttexalens_server_request_type.jtag_read32.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
            )
        )
        return self._check(self._socket.recv())

    def jtag_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBBBBQI",
                ttexalens_server_request_type.jtag_write32.value,
                noc_id,
                chip_id,
                noc_x,
                noc_y,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())

    def jtag_read32_axi(self, chip_id: int, address: int):
        self._socket.send(
            struct.pack(
                "<BBI",
                ttexalens_server_request_type.jtag_read32_axi.value,
                chip_id,
                address,
            )
        )
        return self._check(self._socket.recv())

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBII",
                ttexalens_server_request_type.jtag_write32_axi.value,
                chip_id,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())


class ttexalens_client(TTExaLensCommunicator):
    def __init__(self, address: str, port: int):
        super().__init__()
        self._communication = ttexalens_server_communication(address, port)

        # Check ping/pong to verify it is TTExaLens server on the other end
        pong = self._communication.ping()
        if pong != b"PONG":
            raise ConnectionError()

    def parse_uint32_t(self, buffer: bytes):
        if len(buffer) != 4:
            raise ConnectionError()
        return struct.unpack("<I", buffer)[0]

    def parse_string(self, buffer: bytes):
        return buffer.decode()

    def pci_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.parse_uint32_t(self._communication.pci_read32(noc_id, chip_id, noc_x, noc_y, address))

    def pci_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        buffer = self._communication.pci_write32(noc_id, chip_id, noc_x, noc_y, address, data)
        bytes_written = self.parse_uint32_t(buffer)
        if bytes_written != 4:
            raise ValueError(f"Expected 4 bytes written, but {bytes_written} were written")
        return bytes_written

    def pci_read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        buffer = self._communication.pci_read(noc_id, chip_id, noc_x, noc_y, address, size)
        if len(buffer) != size:
            raise ValueError(f"Expected {size} bytes read, but {len(buffer)} were read")
        return buffer

    def pci_write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        bytes_written = self.parse_uint32_t(self._communication.pci_write(noc_id, chip_id, noc_x, noc_y, address, data))
        if bytes_written != len(data):
            raise ValueError(f"Expected {len(data)} bytes written, but {bytes_written} were written")
        return bytes_written

    def pci_read32_raw(self, chip_id: int, address: int):
        return self.parse_uint32_t(self._communication.pci_read32_raw(chip_id, address))

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        bytes_written = self.parse_uint32_t(self._communication.pci_write32_raw(chip_id, address, data))
        if bytes_written != 4:
            raise ValueError(f"Expected 4 bytes written, but {bytes_written} were written")
        return bytes_written

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        return self.parse_uint32_t(self._communication.dma_buffer_read32(chip_id, address, channel))

    def pci_read_tile(
        self,
        noc_id: int,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        return self.parse_string(
            self._communication.pci_read_tile(noc_id, chip_id, noc_x, noc_y, address, size, data_format)
        )

    def get_cluster_description(self):
        return self.parse_string(self._communication.get_cluster_description())

    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        return self._communication.convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system)

    def get_device_ids(self):
        return self._communication.get_device_ids()

    def get_device_arch(self, chip_id: int):
        return self.parse_string(self._communication.get_device_arch(chip_id))

    def get_device_soc_description(self, chip_id: int):
        return self.parse_string(self._communication.get_device_soc_description(chip_id))

    def get_file(self, file_path: str) -> str:
        return self.parse_string(self._communication.get_file(file_path))

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        binary_content = self._communication.get_file(binary_path)
        return io.BytesIO(binary_content)

    def arc_msg(
        self, noc_id: int, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
    ):
        return self.parse_uint32_t(
            self._communication.arc_msg(noc_id, device_id, msg_code, wait_for_done, arg0, arg1, timeout)
        )
    
    def read_arc_telemetry_entry(self, device_id, telemetry_tag):
        return self.parse_uint32_t(
            self._communication.read_arc_telemetry_entry(device_id, telemetry_tag)
        )

    def jtag_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.parse_uint32_t(self._communication.jtag_read32(noc_id, chip_id, noc_x, noc_y, address))

    def jtag_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self.parse_uint32_t(self._communication.jtag_write32(noc_id, chip_id, noc_x, noc_y, address, data))

    def jtag_read32_axi(self, chip_id: int, address: int):
        return self.parse_uint32_t(self._communication.jtag_read32_axi(chip_id, address))

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        return self.parse_uint32_t(self._communication.jtag_write32_axi(chip_id, address, data))


ttexalens_pybind_path = util.application_path() + "/../build/lib"
binary_path = util.application_path() + "/../build/bin"
sys.path.append(ttexalens_pybind_path)

if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind.so")):
    print(f"Error: 'ttexalens_pybind.so' not found in {ttexalens_pybind_path}. Try: make build")
    sys.exit(1)

# This is a pybind module so we don't need from .
import ttexalens_pybind


class TTExaLensPybind(TTExaLensCommunicator):
    def __init__(self, wanted_devices: list = [], init_jtag=False, initialize_with_noc1=False):
        super().__init__()
        if not ttexalens_pybind.open_device(binary_path, wanted_devices, init_jtag, initialize_with_noc1):
            raise Exception("Failed to open device using pybind library")

    def _check_result(self, result):
        if result is None:
            raise ttexalens_server_not_supported()
        return result

    def pci_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self._check_result(ttexalens_pybind.pci_read32(noc_id, chip_id, noc_x, noc_y, address))

    def pci_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self._check_result(ttexalens_pybind.pci_write32(noc_id, chip_id, noc_x, noc_y, address, data))

    def pci_read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        return self._check_result(ttexalens_pybind.pci_read(noc_id, chip_id, noc_x, noc_y, address, size))

    def pci_write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        return self._check_result(ttexalens_pybind.pci_write(noc_id, chip_id, noc_x, noc_y, address, data, len(data)))

    def pci_read32_raw(self, chip_id: int, address: int):
        return self._check_result(ttexalens_pybind.pci_read32_raw(chip_id, address))

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        return self._check_result(ttexalens_pybind.pci_write32_raw(chip_id, address, data))

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        return self._check_result(ttexalens_pybind.dma_buffer_read32(chip_id, address, channel))

    def pci_read_tile(
        self,
        noc_id: int,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        return self._check_result(
            ttexalens_pybind.pci_read_tile(noc_id, chip_id, noc_x, noc_y, address, size, data_format)
        )

    def get_cluster_description(self):
        return self._check_result(ttexalens_pybind.get_cluster_description())

    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        return self._check_result(ttexalens_pybind.convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system))

    def get_device_ids(self):
        return self._check_result(ttexalens_pybind.get_device_ids())

    def get_device_arch(self, chip_id: int):
        return self._check_result(ttexalens_pybind.get_device_arch(chip_id))

    def get_device_soc_description(self, chip_id: int):
        return self._check_result(ttexalens_pybind.get_device_soc_description(chip_id))

    def jtag_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_read32")
        return self._check_result(ttexalens_pybind.jtag_read32(noc_id, chip_id, noc_x, noc_y, address))

    def jtag_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_write32")
        return self._check_result(ttexalens_pybind.jtag_write32(noc_id, chip_id, noc_x, noc_y, address, data))

    def jtag_read32_axi(self, chip_id: int, address: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_read32_axi")
        return self._check_result(ttexalens_pybind.jtag_read32_axi(chip_id, address))

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_write32_axi")
        return self._check_result(ttexalens_pybind.jtag_write32_axi(chip_id, address, data))

    def get_file(self, file_path: str) -> str:
        content = None
        with open(file_path, "r") as f:
            content = f.read()
        return self._check_result(content)

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        return open(binary_path, "rb")

    def arc_msg(
        self, noc_id: int, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
    ):
        return self._check_result(
            ttexalens_pybind.arc_msg(noc_id, device_id, msg_code, wait_for_done, arg0, arg1, timeout)
        )

    def read_arc_telemetry_entry(self, device_id, telemetry_tag):
        return self._check_result(
            ttexalens_pybind.read_arc_telemetry_entry(device_id, telemetry_tag)
        )


def init_pybind(wanted_devices=None, init_jtag=False, initialize_with_noc1=False):
    if not wanted_devices:
        wanted_devices = []

    communicator = TTExaLensPybind(wanted_devices, init_jtag, initialize_with_noc1)
    util.VERBOSE("Device opened successfully.")
    return communicator


# Spawns ttexalens-server and initializes the communication
def connect_to_server(ip="localhost", port=5555):
    ttexalens_stub_address = f"tcp://{ip}:{port}"
    util.VERBOSE(f"Connecting to ttexalens-server at {ttexalens_stub_address}...")

    try:
        communicator = ttexalens_client(ip, port)
        util.VERBOSE("Connected to ttexalens-server.")
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")

    return communicator
