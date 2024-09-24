third_party/sfpi/compiler/bin/riscv32-unknown-elf-g++ -mwormhole -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 llkd.c -o llkd.elf
third_party/sfpi/compiler/bin/riscv32-unknown-elf-objdump -xsD llkd.elf > llkd.dmp
