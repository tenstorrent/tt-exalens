# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

if not 'DEBUDA_HOME' in os.environ:
	print('DEBUDA_HOME environment variable is not set, trying to autodetect it')
	os.environ['DEBUDA_HOME'] = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip().decode('utf-8')

# Adding the parent directory to the path
sys.path.insert(0, 
				os.path.abspath(
					os.path.join(
						os.environ['DEBUDA_HOME']
						)
					)
				)

from dbd import Verbosity
Verbosity.set(Verbosity.ERROR)
