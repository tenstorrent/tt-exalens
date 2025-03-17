# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

class TTException(Exception):
    pass


# We create a fatal exception that must terminate the program
# All other exceptions might get caught and the program might continue
class TTFatalException(Exception):
    pass