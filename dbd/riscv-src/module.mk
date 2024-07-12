TOOL_PATH?=$(DEBUDA_HOME)/third_party/sfpi/compiler/bin

GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

OPTIONS_ALL=-O0 -mwormhole -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DARCH_WORMHOLE -DTENSIX_FIRMWARE -DLOCAL_MEM_EN=0 -DDEBUG_PRINT_ENABLED -DCOMPILE_FOR_BRISC
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Ldbd/riscv-src

.PHONY: dbd/riscv dbd/riscv/clean

$(OUT)/riscv-src: $(OUT)
	mkdir -p $@

dbd/riscv: $(OUT)/riscv-src $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/brisc-no-globals.elf $(OUT)/riscv-src/brisc-globals.elf $(OUT)/riscv-src/trisc0.elf $(OUT)/riscv-src/trisc1.elf $(OUT)/riscv-src/trisc2.elf

$(OUT)/riscv-src/tmu-crt0.o: dbd/riscv-src/tmu-crt0.S
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

$(OUT)/riscv-src/brisc-no-globals.o: dbd/riscv-src/brisc.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

$(OUT)/riscv-src/brisc-globals.o: dbd/riscv-src/brisc.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DUSE_GLOBAL_VARS -c -o $@ $<

$(OUT)/riscv-src/trisc.o: dbd/riscv-src/trisc.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

$(OUT)/riscv-src/brisc-no-globals.elf: $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/brisc-no-globals.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld $^ -o $@

$(OUT)/riscv-src/brisc-globals.elf: $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/brisc-globals.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/brisc.ld $^ -o $@

$(OUT)/riscv-src/trisc0.elf: $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/trisc.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/trisc0.ld $^ -o $@

$(OUT)/riscv-src/trisc1.elf: $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/trisc.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/trisc1.ld $^ -o $@

$(OUT)/riscv-src/trisc2.elf: $(OUT)/riscv-src/tmu-crt0.o $(OUT)/riscv-src/trisc.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Tdbd/riscv-src/trisc2.ld $^ -o $@

$(OUT)/riscv-src/%.dis: $(OUT)/riscv-src/%.elf
	$(OBJDUMP) -d -s -S $< > $@
	$(OBJDUMP) -t $< | sort >> $@

$(OUT)/riscv-src/%.dump: $(OUT)/riscv-src/%.elf
	$(READELF) --debug-dump $< > $@

dbd/riscv/clean:
	rm -rf $(OUT)/riscv-src
