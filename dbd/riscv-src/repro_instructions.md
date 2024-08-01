# Debug enabled bne error

Note: use modified ``dbd/riscv-src/module.mk`` and ``trisc.cc``

### Expected behavior (this branch)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from budabackend) ``./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_nop_uint8.yaml --seed 0 --silicon``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``riscv status -r 1``  
(expected result) ``HALTED PC=0x00003280 - TRISC0 0,0``

### Observed behavior (a671ef79429ce651c0bcdfa7072769d924281fb4)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from budabackend) ``./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_nop_uint8.yaml --seed 0 --silicon``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``riscv status -r 1``  
(observed result) ``RUNNING - TRISC0 0,0``  
(debuda prompt) ``riscv halt -r 1``  
(observed result) ``Failed to halt TRISC0 core at 0,0``

# Cold start error

Note: use modified ``dbd/riscv-src/module.mk`` and ``trisc.cc``

### Expected behavior1 (this branch)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``riscv status -r 1``  
(expected result) ``HALTED PC=0x00003280 - TRISC0 0,0``

### expected behavior2 (a671ef79429ce651c0bcdfa7072769d924281fb4)

Same as observed behavior for **Debug enabled bne error** except without test_op being run, which shouldnt affect the result

``/home/software/syseng/wh/tt-smi -wr 0``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``riscv status -r 1``  
(expected result) ``RUNNING - TRISC0 0,0``  
(debuda prompt) ``riscv halt -r 1``  
(expected result) ``Failed to halt TRISC0 core at 0,0``

### Observed behavior (a671ef79429ce651c0bcdfa7072769d924281fb4)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(observed result) ``Failed to halt TRISC0 core at 0,0``

# Brisc not being put back in reset error

### Expected behavior (this branch)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from budabackend) ``./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_nop_uint8.yaml --seed 0 --silicon``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``gpr -r 0``  
(expected result) ``Soft reset 1``  

### Observed behavior (a671ef79429ce651c0bcdfa7072769d924281fb4)

``/home/software/syseng/wh/tt-smi -wr 0``  
(from budabackend) ``./build/test/verif/op_tests/test_op --netlist verif/op_tests/netlists/netlist_nop_uint8.yaml --seed 0 --silicon``  
(from debuda) ``./debuda.py``  
(debuda prompt) ``riscv reset 1``  
(debuda prompt) ``re build/riscv-src/trisc0.elf -r 1``  
(debuda prompt) ``riscv reset 0 -r 1``  
(debuda prompt) ``gpr -r 0``  
(observed result) ``Soft reset 0``
