# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Union

__all__ = [
    "tt_lens_init",
    "tt_lens_lib",
    "tt_coordinate",
]

# Setting the verbosity of messages shown
class Verbosity(Enum):
    NONE = 0
    ERROR = 1
    WARN = 2 
    INFO = 3
    VERBOSE = 4
    DEBUG = 5

    @staticmethod
    def set(verbosity: Union[int,"Verbosity"]) -> None:
        '''Set the verbosity level of messages shown.
        
        Args:
            verbosity (int): Verbosity level. 
                1: ERROR
                2: WARN
                3: INFO
                4: VERBOSE
                5: DEBUG
        '''
        global VERBOSITY_VALUE

        VERBOSITY_VALUE = Verbosity(verbosity)

    @staticmethod
    def get() -> "Verbosity":
        '''Get the verbosity level of messages shown.
        
        Returns:
            int: Verbosity level. 
                1: ERROR
                2: WARN
                3: INFO
                4: VERBOSE
                5: DEBUG
        '''
        global VERBOSITY_VALUE

        return VERBOSITY_VALUE

    @staticmethod
    def supports(verbosity: "Verbosity") -> bool:
        '''Check if the verbosity level is supported and should be printed.
        
        Returns:
            bool: True if supported, False otherwise.
        '''
        global VERBOSITY_VALUE

        return VERBOSITY_VALUE.value >= verbosity.value

VERBOSITY_VALUE: Verbosity = Verbosity.INFO
