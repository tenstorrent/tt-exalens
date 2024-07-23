# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

if not os.environ['DEBUDA_HOME']:
	raise Exception('DEBUDA_HOME environment variable is not set')

# Adding the parent directory to the path
sys.path.insert(0, 
				os.path.abspath(
					os.path.join(
						os.environ['DEBUDA_HOME']
						)
					)
				)
