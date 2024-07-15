# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

# Adding the parent directory to the path
sys.path.insert(0, 
				os.path.abspath(
					os.path.join(
						os.path.dirname(__file__), '..'
						)
					)
				)
