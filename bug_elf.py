# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.elf.variable import ElfVariable

context = init_ttexalens()
elf_var = ElfVariable(type_name="long unsigned int", type_tag="base_type", size=4, address=0x467844FAC)
print(elf_var.read_value())
