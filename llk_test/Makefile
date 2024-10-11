TOOL_PATH?=../third_party/sfpi/compiler/bin
OUT ?=build

# Tool paths
GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

# GCC options
OPTIONS_ALL=-O0 -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -L..dbd/riscv-src
INCLUDES = -I../third_party/tt-llk-wh-b0/llk_lib -I../third_party/tt-llk-wh-b0/common/inc -I../third_party/tt-llk-wh-b0/common/inc/sfpu
INCLUDES += -I../third_party/firmware/riscv/common -I../third_party/firmware/riscv/wormhole -I../third_party/firmware/riscv/wormhole/wormhole_b0_defines -I../third_party/firmware/riscv/wormhole/noc -I../third_party/sfpi/include
INCLUDES += -I/usr/include #-L/usr/lib

#$(testname) will be passed by pytest

testname=eltwise_add_test

MINUS_D:="-D"
SPACE:= " "
FORMAT_ARG:=$(MINUS_D)$(format)$(SPACE)
MATHOP_ARG:=$(MINUS_D)$(mathop)$(SPACE)
OPTIONS_COMPILE+=$(FORMAT_ARG) $(MATHOP_ARG)
OPTIONS_COMPILE+=$(INCLUDES)

# Define project paths
RISCV_HELPERS=helpers
RISCV_SOURCE=../dbd/riscv-src
RISCV_OUTPUT=$(OUT)/riscv-src
RISCV_OBJECT=$(OUT)/obj

TEST_OBJ=$(OUT)/obj

# Define architectures and applications
RISCV_ARCHITECTURES := wormhole 
RISCV_APPS := run_elf_test
RISCV_CORES := trisc0 trisc1 trisc2

# Define targets
.PHONY: all clean


all: $(OUT) $(testname)_trisc0.elf $(testname)_trisc1.elf $(testname)_trisc2.elf 

$(OUT):
	mkdir -p $@

$(RISCV_OBJECT): $(OUT)
	mkdir -p $@

$(testname)_trisc0.elf: $(testname)_unpack.o $(RISCV_OBJECT)/tmu-crt0.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $$^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc0.ld -T$(RISCV_SOURCE)/sections.ld -o $$@
$(testname)_trisc1.elf: $(testname)_math.o $(RISCV_OBJECT)/tmu-crt0.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $$^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc1.ld -T$(RISCV_SOURCE)/sections.ld -o $$@
$(testname)_trisc2.elf: $(testname)_pack.o $(RISCV_OBJECT)/tmu-crt0.o
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $$^ -T$(RISCV_SOURCE)/memory.wormhole.ld -T$(RISCV_SOURCE)/trisc2.ld -T$(RISCV_SOURCE)/sections.ld -o $$@

$(testname)_unpack.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_UNPACK -c -o $@ $<
$(testname)_math.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_MATH -c -o $@ $<
$(testname)_pack.o: tests/$(testname).cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -DLLK_TRISC_PACK -c -o $@ $<

clean:
	rm -rf $(OUT)