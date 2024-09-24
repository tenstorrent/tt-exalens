TOOL_PATH=../third_party/sfpi/compiler/bin

BUILD_DIR=build

GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

OPTIONS_ALL=-O3 -mwormhole -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DARCH_WORMHOLE -DTENSIX_FIRMWARE -DLOCAL_MEM_EN=0 -DDEBUG_PRINT_ENABLED -DCOMPILE_FOR_BRISC
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Ldbd/riscv-src
INCLUDES = -I../third_party/tt_llk_wormhole_b0/llk_lib -I../third_party/tt_llk_wormhole_b0/common/inc -I../third_party/tt_llk_wormhole_b0/common/inc/sfpu
INCLUDES += -I../third_party/firmware/riscv/common -I../third_party/firmware/riscv/wormhole -I../third_party/firmware/riscv/wormhole/wormhole_b0_defines -I../third_party/firmware/riscv/wormhole/noc -I../third_party/sfpi/include
DEFINES = -Wl,--defsym=__trisc_base=53248 -Wl,--defsym=__trisc0_size=20480 -Wl,--defsym=__trisc1_size=16384 -Wl,--defsym=__trisc2_size=20480 -Wl,--defsym=__trisc_local_mem_size=4096
OPTIONS_COMPILE += $(INCLUDES)
OPTIONS_LINK += $(DEFINES)

.PHONY: all clean

all: $(BUILD_DIR)/unpack.elf $(BUILD_DIR)/math.elf $(BUILD_DIR)/pack.elf

dis: $(BUILD_DIR)/unpack.dis $(BUILD_DIR)/math.dis $(BUILD_DIR)/pack.dis

$(BUILD_DIR)/%.dis: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(OBJDUMP) -xsD $< > $@
	$(OBJDUMP) -t $< | sort >> $@

$(BUILD_DIR)/%.dump: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(READELF) --debug-dump $< > $@

$(BUILD_DIR)/unpack.elf: $(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/ckernel_unpack.o $(BUILD_DIR)/unpack.o | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Thelpers/trisc0.ld $^ -o $@

$(BUILD_DIR)/math.elf: $(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/ckernel_math.o $(BUILD_DIR)/math.o | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Thelpers/trisc1.ld $^ -o $@

$(BUILD_DIR)/pack.elf: $(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/ckernel_pack.o $(BUILD_DIR)/pack.o | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) -Thelpers/trisc2.ld $^ -o $@

$(BUILD_DIR)/unpack.o: $(BUILD_DIR)/llk.cpp | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_UNPACK -c -o $@ $<

$(BUILD_DIR)/math.o: $(BUILD_DIR)/llk.cpp | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_MATH -c -o $@ $<

$(BUILD_DIR)/pack.o: $(BUILD_DIR)/llk.cpp | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_PACK -c -o $@ $<

$(BUILD_DIR)/ckernel_unpack.o: helpers/ckernel.cc | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DMAILBOX_ADDR=53252 -c -o $@ $<

$(BUILD_DIR)/ckernel_math.o: helpers/ckernel.cc | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DMAILBOX_ADDR=73732 -c -o $@ $<

$(BUILD_DIR)/ckernel_pack.o: helpers/ckernel.cc | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DMAILBOX_ADDR=90116 -c -o $@ $<

$(BUILD_DIR)/tmu-crt0.o: helpers/tmu-crt0.S | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

$(BUILD_DIR):
	mkdir -p $@
	cp tests/unpack_nop_pack_test.cpp $(BUILD_DIR)/llk.cpp

clean:
	rm -rf $(BUILD_DIR)