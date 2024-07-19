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
        Verbosity.VERBOSITY = verbosity
    
    def get():
        return Verbosity.VERBOSITY
        
from os import environ
if environ.get("DEBUDA_VERBOSITY"):
	Verbosity.set(int(environ["DEBUDA_VERBOSITY"]))


