# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from enum import Enum

# An enumeration to specify the format for printing values.
class DATA_FORMAT(Enum):
    HEX = 0
    DEC = 1
    FORMAT = 2  # data type
    BOOL = 3
