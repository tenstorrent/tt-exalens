# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from enum import Enum
import io
import os
import sys
import struct
import zmq

from ttlens import tt_util as util
from ttlens import tt_lens_ifc_cache as tt_lens_ifc_cache
from ttlens.tt_lens_ifc_base import TTLensCommunicator


class ttlens_server_request_type(Enum):
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
    get_harvester_coordinate_translation = 17
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
    get_runtime_data = 101
    get_cluster_description = 102

    # File requests
    get_file = 200
    get_buda_run_dirpath = 201


class ttlens_server_bad_request(Exception):
    pass


class ttlens_server_not_supported(Exception):
    pass


class ttlens_server_communication:
    """
    This class handles the communication with the TTLens server using ZMQ. It is responsible for sending requests and
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
        if response == ttlens_server_communication._BAD_REQUEST:
            raise ttlens_server_bad_request()
        if response == ttlens_server_communication._NOT_SUPPORTED:
            raise ttlens_server_not_supported()
        return response

    def ping(self):
        self._socket.send(bytes([ttlens_server_request_type.ping.value]))
        return self._check(self._socket.recv())

    def pci_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        self._socket.send(
            struct.pack(
                "<BBBBQ",
                ttlens_server_request_type.pci_read32.value,
                chip_id,
                noc_x,
                noc_y,
                address,
            )
        )
        return self._check(self._socket.recv())

    def pci_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBBBQI",
                ttlens_server_request_type.pci_write32.value,
                chip_id,
                noc_x,
                noc_y,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())

    def pci_read(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        self._socket.send(
            struct.pack(
                "<BBBBQI",
                ttlens_server_request_type.pci_read.value,
                chip_id,
                noc_x,
                noc_y,
                address,
                size,
            )
        )
        return self._check(self._socket.recv())

    def pci_write(
        self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes
    ):
        self._socket.send(
            struct.pack(
                f"<BBBBQI{len(data)}s",
                ttlens_server_request_type.pci_write.value,
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
        self._socket.send(
            struct.pack(
                "<BBI", ttlens_server_request_type.pci_read32_raw.value, chip_id, address
            )
        )
        return self._check(self._socket.recv())

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBII",
                ttlens_server_request_type.pci_write32_raw.value,
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
                ttlens_server_request_type.dma_buffer_read32.value,
                chip_id,
                address,
                channel,
            )
        )
        return self._check(self._socket.recv())

    def pci_read_tile(
        self,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        self._socket.send(
            struct.pack(
                "<BBBBQIB",
                ttlens_server_request_type.pci_read_tile.value,
                chip_id,
                noc_x,
                noc_y,
                address,
                size,
                data_format,
            )
        )
        return self._check(self._socket.recv())

    def get_runtime_data(self):
        self._socket.send(
            bytes([ttlens_server_request_type.get_runtime_data.value]))
        return self._check(self._socket.recv())

    def get_cluster_description(self):
        self._socket.send(
            bytes([ttlens_server_request_type.get_cluster_description.value])
        )
        return self._check(self._socket.recv())

    def get_harvester_coordinate_translation(self, chip_id: int):
        self._socket.send(
            struct.pack(
                "<BB",
                ttlens_server_request_type.get_harvester_coordinate_translation.value,
                chip_id,
            )
        )
        return self._check(self._socket.recv())

    def get_device_ids(self):
        self._socket.send(
            bytes([ttlens_server_request_type.get_device_ids.value])
        )
        return self._check(self._socket.recv())

    def get_device_arch(self, chip_id: int):
        self._socket.send(
            struct.pack(
                "<BB",
                ttlens_server_request_type.get_device_arch.value,
                chip_id,
            )
        )
        return self._check(self._socket.recv())

    def get_device_soc_description(self, chip_id: int):
        self._socket.send(
            struct.pack(
                "<BB",
                ttlens_server_request_type.get_device_soc_description.value,
                chip_id,
            )
        )
        return self._check(self._socket.recv())

    def get_file(self, path: str):
        encoded_path = path.encode()
        self._socket.send(
            struct.pack(
                f"<BI{len(encoded_path)}s",
                ttlens_server_request_type.get_file.value,
                len(encoded_path),
                encoded_path,
            )
        )
        return self._check(self._socket.recv())

    def get_run_dirpath(self):
        self._socket.send(
            bytes([ttlens_server_request_type.get_buda_run_dirpath.value])
        )
        return self._check(self._socket.recv())

    def arc_msg(self, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int):
        self._socket.send(
            struct.pack(
                "<BBBIIIIB",
                ttlens_server_request_type.arc_msg.value,
                device_id,
                msg_code,
                wait_for_done,
                arg0,
                arg1,
                timeout
            )
        )
        return self._check(self._socket.recv())

    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        self._socket.send(
            struct.pack(
                "<BBBBQ",
                ttlens_server_request_type.jtag_read32.value,
                chip_id,
                noc_x,
                noc_y,
                address,
            )
        )
        return self._check(self._socket.recv())

    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBBBQI",
                ttlens_server_request_type.jtag_write32.value,
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
                ttlens_server_request_type.jtag_read32_axi.value,
                chip_id,
                address,
            )
        )
        return self._check(self._socket.recv())

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        self._socket.send(
            struct.pack(
                "<BBII",
                ttlens_server_request_type.jtag_write32_axi.value,
                chip_id,
                address,
                data,
            )
        )
        return self._check(self._socket.recv())


class ttlens_client(TTLensCommunicator):
    def __init__(self, address: str, port: int):
        super().__init__()
        self._communication = ttlens_server_communication(address, port)

        # Check ping/pong to verify it is TTLens server on the other end
        pong = self._communication.ping()
        if pong != b"PONG":
            raise ConnectionError()

    def parse_uint32_t(self, buffer: bytes):
        if len(buffer) != 4:
            raise ConnectionError()
        return struct.unpack("<I", buffer)[0]

    def parse_string(self, buffer: bytes):
        return buffer.decode()

    def pci_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.parse_uint32_t(
            self._communication.pci_read32(chip_id, noc_x, noc_y, address)
        )

    def pci_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        buffer = self._communication.pci_write32(
            chip_id, noc_x, noc_y, address, data)
        bytes_written = self.parse_uint32_t(buffer)
        if bytes_written != 4:
            raise ValueError(
                f"Expected 4 bytes written, but {bytes_written} were written"
            )
        return bytes_written

    def pci_read(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        buffer = self._communication.pci_read(
            chip_id, noc_x, noc_y, address, size)
        if len(buffer) != size:
            raise ValueError(
                f"Expected {size} bytes read, but {len(buffer)} were read")
        return buffer

    def pci_write(
        self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes
    ):
        bytes_written = self.parse_uint32_t(
            self._communication.pci_write(chip_id, noc_x, noc_y, address, data)
        )
        if bytes_written != len(data):
            raise ValueError(
                f"Expected {len(data)} bytes written, but {bytes_written} were written"
            )
        return bytes_written

    def pci_read32_raw(self, chip_id: int, address: int):
        return self.parse_uint32_t(self._communication.pci_read32_raw(chip_id, address))

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        bytes_written = self.parse_uint32_t(
            self._communication.pci_write32_raw(chip_id, address, data)
        )
        if bytes_written != 4:
            raise ValueError(
                f"Expected 4 bytes written, but {bytes_written} were written"
            )
        return bytes_written

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        return self.parse_uint32_t(
            self._communication.dma_buffer_read32(chip_id, address, channel)
        )

    def pci_read_tile(
        self,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        return self.parse_string(
            self._communication.pci_read_tile(
                chip_id, noc_x, noc_y, address, size, data_format
            )
        )

    def get_runtime_data(self):
        return self.parse_string(self._communication.get_runtime_data())

    def get_cluster_description(self):
        return self.parse_string(self._communication.get_cluster_description())

    def get_harvester_coordinate_translation(self, chip_id: int):
        return self.parse_string(
            self._communication.get_harvester_coordinate_translation(chip_id)
        )

    def get_device_ids(self):
        return self._communication.get_device_ids()

    def get_device_arch(self, chip_id: int):
        return self.parse_string(
            self._communication.get_device_arch(chip_id)
        )

    def get_device_soc_description(self, chip_id: int):
        return self.parse_string(
            self._communication.get_device_soc_description(chip_id)
        )

    def get_file(self, file_path: str) -> str:
        return self.parse_string(
            self._communication.get_file(file_path)
        )

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        binary_content = self._communication.get_file(binary_path)
        return io.BytesIO(binary_content)

    def get_run_dirpath(self) -> str:
        run_dirpath = self.parse_string(
            self._communication.get_run_dirpath()
        )
        if run_dirpath != "":
            return run_dirpath
        return None

    def arc_msg(self, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int):
        return self.parse_uint32_t(
            self._communication.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout)
        )

    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.parse_uint32_t(
            self._communication.jtag_read32(chip_id, noc_x, noc_y, address)
        )

    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self.parse_uint32_t(
            self._communication.jtag_write32(chip_id, noc_x, noc_y, address, data)
        )

    def jtag_read32_axi(self, chip_id: int, address: int):
        return self.parse_uint32_t(
            self._communication.jtag_read32_axi(chip_id, address)
        )

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        return self.parse_uint32_t(
            self._communication.jtag_write32_axi(chip_id, address, data)
        )


ttlens_pybind_path = util.application_path() + "/../build/lib"
binary_path = util.application_path() + "/../build/bin"
sys.path.append(ttlens_pybind_path)

if not os.path.isfile(os.path.join(ttlens_pybind_path, "ttlens_pybind.so")):
    print(f"Error: 'ttlens_pybind.so' not found in {ttlens_pybind_path}. Try: make build")
    sys.exit(1)

# This is a pybind module so we don't need from .
import ttlens_pybind


class TTLensPybind(TTLensCommunicator):
    def __init__(self, runtime_data_yaml_filename: str = "", run_dirpath: str = None, wanted_devices: list = []):
        super().__init__()
        if not ttlens_pybind.open_device(binary_path, runtime_data_yaml_filename, wanted_devices):
            raise Exception("Failed to open device using pybind library")
        self._runtime_yaml_path = runtime_data_yaml_filename # Don't go through C++ for opening files
        self._run_dirpath = run_dirpath

    def _check_result(self, result):
        if result is None:
            raise ttlens_server_not_supported()
        return result

    def pci_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self._check_result(ttlens_pybind.pci_read32(chip_id, noc_x, noc_y, address))

    def pci_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self._check_result(ttlens_pybind.pci_write32(chip_id, noc_x, noc_y, address, data))

    def pci_read(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        return self._check_result(ttlens_pybind.pci_read(chip_id, noc_x, noc_y, address, size))

    def pci_write(
        self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes
    ):
        return self._check_result(ttlens_pybind.pci_write(chip_id, noc_x, noc_y, address, data, len(data)))

    def pci_read32_raw(self, chip_id: int, address: int):
        return self._check_result(ttlens_pybind.pci_read32_raw(chip_id, address))

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        return self._check_result(ttlens_pybind.pci_write32_raw(chip_id, address, data))

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        return self._check_result(ttlens_pybind.dma_buffer_read32(chip_id, address, channel))

    def pci_read_tile(
        self,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        return self._check_result(ttlens_pybind.pci_read_tile(chip_id, noc_x, noc_y, address, size, data_format))

    def get_runtime_data(self) -> str:
        if self._runtime_yaml_path:
            with open(self._runtime_yaml_path, 'r') as f:
                return f.read()
        else: raise ttlens_server_not_supported()

    def get_cluster_description(self):
        return self._check_result(ttlens_pybind.get_cluster_description())

    def get_harvester_coordinate_translation(self, chip_id: int):
        return self._check_result(ttlens_pybind.get_harvester_coordinate_translation(chip_id))

    def get_device_ids(self):
        return self._check_result(ttlens_pybind.get_device_ids())

    def get_device_arch(self, chip_id: int):
        return self._check_result(ttlens_pybind.get_device_arch(chip_id))

    def get_device_soc_description(self, chip_id: int):
        return self._check_result(ttlens_pybind.get_device_soc_description(chip_id))

    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self._check_result(ttlens_pybind.jtag_read32(chip_id, noc_x, noc_y, address))

    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self._check_result(ttlens_pybind.jtag_write32(chip_id, noc_x, noc_y, address, data))

    def jtag_read32_axi(self, chip_id: int, address: int):
        return self._check_result(ttlens_pybind.jtag_read32_axi(chip_id, address))

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        return self._check_result(ttlens_pybind.jtag_write32_axi(chip_id, address, data))

    def get_file(self, file_path: str) -> str:
        content = None
        with open(file_path, 'r') as f:
            content = f.read()
        return self._check_result(content)

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        return open(binary_path, 'rb')

    def get_run_dirpath(self) -> str:
        return self._run_dirpath

    def arc_msg(self, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int):
        return self._check_result(ttlens_pybind.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout))

def init_pybind(runtime_data_yaml_filename, run_dirpath=None, wanted_devices=None):
    if not wanted_devices:
        wanted_devices = []

    communicator = TTLensPybind(runtime_data_yaml_filename, run_dirpath, wanted_devices)
    util.VERBOSE("Device opened successfully.")
    return communicator


# Spawns ttlens-server and initializes the communication
def connect_to_server(ip="localhost", port=5555):
    ttlens_stub_address = f"tcp://{ip}:{port}"
    util.VERBOSE(f"Connecting to ttlens-server at {ttlens_stub_address}...")

    try:
        communicator = ttlens_client(ip, port)
        util.VERBOSE("Connected to ttlens-server.")
    except:
        raise util.TTFatalException("Failed to connect to TTLens server.")

    return communicator
