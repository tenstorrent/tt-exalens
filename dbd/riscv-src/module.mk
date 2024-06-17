TOOL_PATH?=$(DEBUDA_HOME)/third_party/sfpi/compiler/bin

GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

OPTIONS_ALL=-O0 -mwormhole -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DARCH_WORMHOLE -DTENSIX_FIRMWARE -DLOCAL_MEM_EN=0 -DDEBUG_PRINT_ENABLED -DCOMPILE_FOR_BRISC
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles

dbd/riscv:
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o dbd/riscv-src/tmu-crt0.o dbd/riscv-src/tmu-crt0.S
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o dbd/riscv-src/brisc-no-globals.o dbd/riscv-src/brisc.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DUSE_GLOBAL_VARS -c -o dbd/riscv-src/brisc-globals.o dbd/riscv-src/brisc.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld dbd/riscv-src/tmu-crt0.o dbd/riscv-src/brisc-no-globals.o -o dbd/riscv-src/brisc-no-globals.elf
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld dbd/riscv-src/tmu-crt0.o dbd/riscv-src/brisc-globals.o -o dbd/riscv-src/brisc-globals.elf
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld dbd/riscv-src/tmu-crt0.o dbd/riscv-src/brisc-no-globals.o -o dbd/riscv-src/brisc-no-globals.elf
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld dbd/riscv-src/tmu-crt0.o dbd/riscv-src/brisc-globals.o -o dbd/riscv-src/brisc-globals.elf
	$(READELF) --debug-dump ./dbd/riscv-src/brisc-no-globals.elf > dbd/riscv-src/brisc-no-globals.elf.dump
	$(READELF) --debug-dump ./dbd/riscv-src/brisc-globals.elf > dbd/riscv-src/brisc-globals.elf.dump
	$(OBJDUMP) -d -s -S dbd/riscv-src/brisc-no-globals.elf > dbd/riscv-src/brisc-no-globals.dis
	$(OBJDUMP) -t dbd/riscv-src/brisc-no-globals.elf | sort >> dbd/riscv-src/brisc-no-globals.dis
	$(OBJDUMP) -d -s -S dbd/riscv-src/brisc-globals.elf > dbd/riscv-src/brisc-globals.dis
	$(OBJDUMP) -t dbd/riscv-src/brisc-globals.elf | sort >> dbd/riscv-src/brisc-globals.dis

clean_dbd_riscv:
	rm -f dbd/riscv-src/*.o
	rm -f dbd/riscv-src/*.dis
	rm -f dbd/riscv-src/*.elf
	rm -f dbd/riscv-src/*.dump
