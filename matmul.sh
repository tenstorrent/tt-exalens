cd /home/software/syseng/wh
./tt-smi -wr 0
cd /localdev/ldjurovic/tt-debuda/llk_test
make clean
make dis format=FORMAT_FLOAT16_B mathop=ELTWISE_BINARY_ADD
cd ..
./debuda.py --commands \
"riscv reset 1; 
re llk_test/build/unpack.elf -r 1;
re llk_test/build/math.elf -r 2;
re llk_test/build/pack.elf -r 3;
riscv reset 0;
riscv status -r 1;
riscv status -r 2;
riscv status -r 3;
brxy 18-18 0xfa40 256;
brxy 18-18 0xea40 256;
brxy 18-18 0x17d50 256;
brxy 18-18 0xd004;
brxy 18-18 0x12004;
brxy 18-18 0x16004;
exit"