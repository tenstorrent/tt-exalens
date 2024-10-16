TOOL_PATH?=../third_party/sfpi/compiler/bin
BUILD_DIR ?=build

# Tool paths
GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

# GCC options
OPTIONS_ALL=-O3 -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -ffast-math -flto
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DARCH_WORMHOLE -DTENSIX_FIRMWARE -DDEBUG_PRINT_ENABLED
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -L../dbd/riscv-src -Wl,--trace
INCLUDES = -I../third_party/tt-llk-wh-b0/llk_lib -I../third_party/tt-llk-wh-b0/common/inc -I../third_party/tt-llk-wh-b0/common/inc/sfpu
INCLUDES += -I../third_party/firmware/riscv/common -I../third_party/firmware/riscv/wormhole -I../third_party/firmware/riscv/wormhole/wormhole_b0_defines -I../third_party/firmware/riscv/wormhole/noc -I../third_party/sfpi/include

MINUS_D:="-D"
SPACE:= " "
FORMAT_ARG:=$(MINUS_D)$(format)$(SPACE)
MATHOP_ARG:=$(MINUS_D)$(mathop)$(SPACE)
OPTIONS_COMPILE+=$(FORMAT_ARG) $(MATHOP_ARG)
OPTIONS_COMPILE+=$(INCLUDES)
OPTIONS_ALL+=-m$(machine)

# Define project paths
RISCV_SOURCE=../dbd/riscv-src
OUTPUT_ELFS = $(BUILD_DIR)/elf

# Define targets
.PHONY: all clean

all: $(BUILD_DIR) $(OUTPUT_ELFS) $(OUTPUT_ELFS)/$(testname)_trisc0.elf $(OUTPUT_ELFS)/$(testname)_trisc1.elf $(OUTPUT_ELFS)/$(testname)_trisc2.elf 
dis: $(BUILD_DIR)/$(testname)_trisc0.dis $(BUILD_DIR)/$(testname)_trisc1.dis $(BUILD_DIR)/$(testname)_trisc2.dis

$(BUILD_DIR)/%.dis :  $(OUTPUT_ELFS)/%.elf
	$(OBJDUMP) -xsD $< > $@
	$(OBJDUMP) -t $< | sort >> $@

$(BUILD_DIR):
	mkdir -p $@

$(OUTPUT_ELFS): $(BUILD_DIR)
	mkdir -p $@

# Buiding .elf files for every TRISC core
 $(OUTPUT_ELFS)/$(testname)_trisc0.elf :$(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/main_unpack.o $(BUILD_DIR)/$(testname)_unpack.o 
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc0.ld -T$(RISCV_SOURCE)/sections.ld -o $@
 $(OUTPUT_ELFS)/$(testname)_trisc1.elf: $(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/main_math.o $(BUILD_DIR)/$(testname)_math.o 
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc1.ld -T$(RISCV_SOURCE)/sections.ld -o $@
 $(OUTPUT_ELFS)/$(testname)_trisc2.elf: $(BUILD_DIR)/tmu-crt0.o $(BUILD_DIR)/main_pack.o $(BUILD_DIR)/$(testname)_pack.o 
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc2.ld -T$(RISCV_SOURCE)/sections.ld -o $@

#compiling _test.cc to .o
$(BUILD_DIR)/$(testname)_unpack.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_UNPACK -c -o $@ $<
$(BUILD_DIR)/$(testname)_math.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_MATH -c -o $@ $<
$(BUILD_DIR)/$(testname)_pack.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_PACK -c -o $@ $<

#compiling main for every TRISC core
$(BUILD_DIR)/main_unpack.o : helpers/run_elf_test.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_UNPACK -c -o $@ $<
$(BUILD_DIR)/main_math.o : helpers/run_elf_test.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_MATH -c -o $@ $<
$(BUILD_DIR)/main_pack.o : helpers/run_elf_test.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_PACK -c -o $@ $<	

$(BUILD_DIR)/tmu-crt0.o: $(RISCV_SOURCE)/tmu-crt0.S | $(BUILD_DIR)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

clean:
	rm -rf $(BUILD_DIR)