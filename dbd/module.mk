GIT_ROOT?=$(shell git rev-parse --show-toplevel)
include $(GIT_ROOT)/dbd/util.mk

# Every variable in subdir must be prefixed with subdir(emulating a namespace)

DBD_INCLUDES = $(BASE_INCLUDES) $(GOLDEN_INCLUDES) $(MODEL2_INCLUDES) $(NETLIST_INCLUDES) $(MODEL_INCLUDES) -Iverif/directed_tests -Iverif -Ithird_party/json
DBD_LIB = $(LIBDIR)/libdbd.a
DBD_DEFINES = -DGIT_HASH=$(shell git rev-parse HEAD)
DBD_INCLUDES += -Imodel -Inetlist -Icommon -Iversim/$(ARCH_NAME)/headers/vendor/yaml-cpp/include -Isrc/firmware/riscv/$(ARCH_NAME)/
DBD_CFLAGS = $(CFLAGS) -Werror
DBD_LDFLAGS = -ltt -ldevice -lstdc++fs -lpthread -lyaml-cpp -lcommon -lboost_program_options

DBD_SRCS = $(wildcard dbd/*.cpp)

DBD_OBJS = $(addprefix $(OBJDIR)/, $(DBD_SRCS:.cpp=.o))
DBD_DEPS = $(addprefix $(OBJDIR)/, $(DBD_SRCS:.cpp=.d))

DEBUDA_STUB_TARGET = $(BINDIR)/debuda-stub
DEBUDA_STUB_SRC = model/tile.cpp device/tt_silicon_driver_debuda_stub.cpp device/tt_silicon_driver_common.cpp device/tt_silicon_driver.cpp model/tt_rnd_util.cpp device/tt_device.cpp
DEBUDA_STUB_INCLUDES = -Isrc/firmware/riscv/$(ARCH_NAME)/
DEBUDA_STUB_LDFLAGS = -lzmq -lpthread ./device/lib/libyaml-cpp.a

ifeq ("$(ARCH_NAME)", "wormhole_b0")
  DEBUDA_STUB_SRC += device/wormhole/impl_device.cpp
  DEBUDA_STUB_INCLUDES += -Idevice/wormhole/
else ifeq ("$(ARCH_NAME)", "wormhole")
  DEBUDA_STUB_SRC += device/wormhole/impl_device.cpp
  DEBUDA_STUB_INCLUDES += -Idevice/wormhole/
else
  DEBUDA_STUB_SRC += device/grayskull/impl_device.cpp
  DEBUDA_STUB_INCLUDES += -Idevice/grayskull/
endif

-include $(DBD_DEPS)

dbd: $(OUT)/bin/dbd_modify_netlist dbd/debuda-stub
	$(PRINT_TARGET)
	$(PRINT_OK)

dbd/debuda-stub: $(DEBUDA_STUB_TARGET)
	$(PRINT_TARGET)
	$(PRINT_OK)

$(DEBUDA_STUB_TARGET): $(DEBUDA_STUB_SRC)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DEBUDA_STUB_INCLUDES) -o $@ $^ $(LDFLAGS) $(DEBUDA_STUB_LDFLAGS)
	$(PRINT_OK)

dbd/clean:
	-rm $(OUT)/bin/dbd_* $(SILENT_ERRORS)
	-rm $(DEBUDA_STUB) $(SILENT_ERRORS)
	-rm $(OBJDIR)/dbd/* $(SILENT_ERRORS)

$(DBD_LIB): $(DBD_OBJS) $(BACKEND_LIB)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	ar rcs -o $@ $(DBD_OBJS)
	$(PRINT_OK)

$(OUT)/bin/dbd_%: $(OBJDIR)/dbd/%.o $(BACKEND_LIB) $(DBD_LIB) $(VERIF_LIB)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DBD_INCLUDES) -o $@ $^ $(LDFLAGS) $(DBD_LDFLAGS)
	$(PRINT_OK)

$(OBJDIR)/dbd/%.o: dbd/%.cpp
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(DBD_CFLAGS) $(CXXFLAGS) $(STATIC_LIB_FLAGS) $(DBD_INCLUDES) $(DBD_DEFINES) -c -o $@ $<
	$(PRINT_OK)

include dbd/tools/module.mk
