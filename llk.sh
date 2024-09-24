./debuda.py --commands \
"riscv reset 1; 
brxy 18-18 0xd1f0;
brxy 18-18 0x161f0;
re llk_test/build/unpack.elf -r 1;
re llk_test/build/math.elf -r 2;
re llk_test/build/pack.elf -r 3;
riscv reset 0;
riscv status -r 1;
riscv status -r 2;
riscv status -r 3;
brxy 18-18 0xd004;
brxy 18-18 0x12004;
brxy 18-18 0x16004;
brxy 18-18 0xd1ec;
brxy 18-18 0xe1f0 256;
brxy 18-18 0x121ec;
brxy 18-18 0x121f0 256;
brxy 18-18 0x161ec;
brxy 18-18 0x171f0 256;
brxy 18-18 0xd1f0 1024;
brxy 18-18 0x161f0 1024;
exit"