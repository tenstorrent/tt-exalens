# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.tt_exalens_lib import convert_coordinate, read_word_from_device
from ttexalens.umd_device import TimeoutDeviceRegisterError

location = convert_coordinate("0,0")
for address in range(0xFF000000, 0xFFFFFFFF, 4):
    if address % (1024 * 1024) == 0:
        print(f"Probing address {address/1024/1024}MB...")
    try:
        value = read_word_from_device(location, address, safe_mode=False)
    except TimeoutDeviceRegisterError as e:
        print(str(e))
