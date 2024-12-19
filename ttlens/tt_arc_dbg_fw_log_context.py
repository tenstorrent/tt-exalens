# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import yaml, os
from ttlens.tt_util import TTException
from typing import List, Union
from abc import ABC, abstractmethod


class LogInfo:
    """
    A class representing an ARC DFW log info
    """

    def __init__(self, address=0, log_name="", size=0, output="int"):
        self.address = address
        self.log_name = log_name
        self.size = size
        self.output = output


class ArcDfwLogContext(ABC):
    def __init__(self, log_configuration: Union[str, List[str]], log_yaml_file: str = "fw/arc/log/default.yaml"):
        """
        Args:
            log_configuration: Either a string representing the name of the log configuration to use, or a list of log names
            log_yaml_file: The path to the yaml file containing the log configuration

        Raises:
            TTException: If the log_configuration is not a string or list
        """
        self.log_list = []
        yaml_data = self.__parse_yaml(log_yaml_file)

        # Hardcoding heartbeat address because it's used as timestamp
        self.log_list.append(LogInfo(address=self._parse_address(yaml_data, "heartbeat"), log_name="heartbeat"))

        self.parse(yaml_data, log_configuration)

        if len(self.log_list) == 0:
            raise TTException(f"No logs found for configuration {log_configuration}")

    def _parse_address(self, yaml_data: dict, log_name) -> int:
        """
        Parse the address of the log from the yaml file

        Args:
            yaml_data: The data from the yaml file
            log_name: The name of the log to get the address for

        Returns:
            int: The address of the log
        """

        if log_name not in yaml_data["record_configurations"]:
            raise TTException(f"Address for log {log_name} not found in yaml file")

        addr_str = yaml_data["record_configurations"][log_name]["address"]

        if addr_str.find("+") != -1:
            addr_str = addr_str.replace(" ", "").split("+")
            return yaml_data["base_addresses"][addr_str[0]] + int(addr_str[1], 16)
        else:
            return int(addr_str, 16)

    def __parse_yaml(self, log_yaml_file: str) -> dict:
        """
        Parse the yaml file

        Args:
            log_yaml_file: The path to the yaml file

        Returns:
            dict: The data from the yaml file
        """
        yaml_data = {}
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_yaml_file)
        with open(file_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        return yaml_data

    @abstractmethod
    def parse(self, yaml_data: dict, log_configuration: Union[str, List[str]]) -> list:
        """
        Parse the log configuration and returns a list LogInfo objects which contains the address, log name, size and output type

        Args:
            yaml_data: The data from the yaml file
            log_configuration: Either a string representing the name of the log configuration to use, or a list of log names

        Returns:
            list: A list of LogInfo objects
        """
        pass


class ArcDfwLogContextFromYaml(ArcDfwLogContext):
    def parse(self, yaml_data: dict, log_configuration: str) -> list:
        if not isinstance(log_configuration, str):
            raise TTException(f"Expected a string for log configuration, got {type(log_configuration)}")

        for log in yaml_data["logger_configuration"][log_configuration]:
            if log == "heartbeat":
                continue
            size = yaml_data["record_configurations"][log]["size"]
            output = yaml_data["record_configurations"][log]["output"]
            self.log_list.append(
                LogInfo(address=self._parse_address(yaml_data, log), log_name=log, size=size, output=output)
            )


class ArcDfwLogContextFromList(ArcDfwLogContext):
    def parse(self, yaml_data: dict, log_list: List[str]) -> list:
        if not isinstance(log_list, list):
            raise TTException(f"Expected a list of log names, got {type(log_list)}")

        for log in log_list:
            if log == "heartbeat":
                continue
            size = yaml_data["record_configurations"][log]["size"]
            output = yaml_data["record_configurations"][log]["output"]
            self.log_list.append(
                LogInfo(address=self._parse_address(yaml_data, log), log_name=log, size=size, output=output)
            )
