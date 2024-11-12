TOOL_PATH?=$(DEBUDA_HOME)/third_party/sfpi/compiler/bin

# Tool paths
GXX=$(TOOL_PATH)/riscv32-unknown-elf-g++
OBJDUMP=$(TOOL_PATH)/riscv32-unknown-elf-objdump
OBJCOPY=$(TOOL_PATH)/riscv32-unknown-elf-objcopy
READELF=$(TOOL_PATH)/riscv32-unknown-elf-readelf

# GCC options
OPTIONS_ALL=-O0 -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math
OPTIONS_COMPILE=-fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable
OPTIONS_LINK=-fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Ldbd/riscv-src

# Define project paths
RISCV_SOURCE=ttlens/riscv-src
RISCV_OUTPUT=$(OUT)/riscv-src
RISCV_OBJECT=$(OUT)/obj/riscv-src

# Define architectures and applications
RISCV_ARCHITECTURES := grayskull wormhole blackhole
RISCV_APPS := sample run_elf_test
RISCV_CORES := brisc trisc0 trisc1 trisc2 ncrisc

# Define targets
.PHONY: ttlens/riscv ttlens/riscv/clean

$(RISCV_OBJECT): $(OUT)
	mkdir -p $@

ttlens/riscv: $(RISCV_OBJECT) ttlens/riscv/grayskull ttlens/riscv/wormhole ttlens/riscv/blackhole

ttlens/riscv/clean:
	rm -rf $(RISCV_OBJECT)
	rm -rf $(RISCV_OUTPUT)

# CRT compile target (assembly)
$(RISCV_OBJECT)/tmu-crt0.o: $(RISCV_SOURCE)/tmu-crt0.S
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

# C++ compile target
$(RISCV_OBJECT)/%.o: $(RISCV_SOURCE)/%.cc
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_COMPILE) -c -o $@ $<

# Define function that creates target for selected architecture and selected application and selected core
#   $(1) - architecture
#   $(2) - application
#   $(3) - core
define create_riscv_core_target
$(RISCV_OUTPUT)/$(1)/$(2).$(3).elf: $(RISCV_OBJECT)/tmu-crt0.o $(RISCV_OBJECT)/$(2).o
	mkdir -p $(RISCV_OUTPUT)/$(1)
	$(GXX) $(OPTIONS_ALL) $(OPTIONS_LINK) $$^ -T$(RISCV_SOURCE)/memory.$(1).ld -T$(RISCV_SOURCE)/$(3).ld -T$(RISCV_SOURCE)/sections.ld -o $$@
	$(OBJDUMP) -d -s -S $(RISCV_OUTPUT)/$(1)/$(2).$(3).elf > $(RISCV_OUTPUT)/$(1)/$(2).$(3).dump
	$(OBJDUMP) -t $(RISCV_OUTPUT)/$(1)/$(2).$(3).elf | sort >> $(RISCV_OUTPUT)/$(1)/$(2).$(3).dump
	$(READELF) --debug-dump $(RISCV_OUTPUT)/$(1)/$(2).$(3).elf > $(RISCV_OUTPUT)/$(1)/$(2).$(3).dis
endef

# Define funciton that creates target for selected architecture and selected application and all cores
#   $(1) - architecture
#   $(2) - application
#   $(3) - list of cores
define create_riscv_application
	$(foreach core,$(3),$(eval $(call create_riscv_core_target,$(1),$(2),$(core))))
endef

# Define function that creates target for selected architecture and all applications and all cores
#   $(1) - architecture
#   $(2) - list of applications
#   $(3) - list of cores
define create_riscv_target
	$(foreach app,$(2),$(call create_riscv_application,$(1),$(app),$(3)))
ttlens/riscv/$(1): $(foreach app,$(2),$(foreach core,$(3),$(RISCV_OUTPUT)/$(1)/$(app).$(core).elf))
endef

# Define function that creates targets for each architecture and all application and all cores
#   $(1) - list of architectures
#   $(2) - list of applications
#	$(3) - list of cores
define create_riscv_targets
	$(foreach arch,$(1),$(eval $(call create_riscv_target,$(arch),$(2),$(3))))
endef

# Call function that creates targets for all architectures and all applications and all cores
$(call create_riscv_targets,$(RISCV_ARCHITECTURES),$(RISCV_APPS),$(RISCV_CORES))
