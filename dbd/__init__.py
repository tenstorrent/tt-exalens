# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
__all__ = [
	"tt_debuda_init",
	"tt_debuda_lib",
	"tt_coordinate",
]


# Setting the verbosity of messages shown
class Verbosity():
    ERROR = 1
    WARN = 2 
    DEBUG = 3
    INFO = 4
    VERBOSE = 5
    
    VERBOSITY: int = ERROR
    
    def set(verbosity: int):
        '''Set the verbosity level of messages shown.
        
        Args:
            verbosity (int): Verbosity level. 
                1: ERROR
                2: WARN
                3: DEBUG
                4: INFO
                5: VERBOSE
        '''
        Verbosity.VERBOSITY = verbosity
    
    def get() -> int:
        '''Get the verbosity level of messages shown.
        
        Returns:
            int: Verbosity level. 
                1: ERROR
                2: WARN
                3: DEBUG
                4: INFO
                5: VERBOSE
        '''
        return Verbosity.VERBOSITY

