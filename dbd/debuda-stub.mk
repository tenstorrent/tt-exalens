DEBUDA_STUB_TARGET = $(BINDIR)/debuda-stub

DEBUDA_STUB_SRC = device/tt_silicon_driver_debuda_stub.cpp

DEBUDA_STUB_SRC += 								\
	model/tile.cpp 								\
	model/tt_rnd_util.cpp 						\
	device/tt_silicon_driver_debuda_stub.cpp 	\
	device/tt_silicon_driver_common.cpp 		\
	device/tt_silicon_driver.cpp 				\
	device/tt_device.cpp

DEBUDA_STUB_INCLUDES = -Isrc/firmware/riscv/$(ARCH_NAME)/

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

DEBUDA_STUB_OBJS = $(addprefix $(OBJDIR)/, $(DEBUDA_STUB_SRC:.cpp=.o))
DEBUDA_STUB_DEPS = $(addprefix $(OBJDIR)/, $(DEBUDA_STUB_SRC:.cpp=.d))

DEBUDA_STUB_LDFLAGS = -lzmq -lpthread -lyaml-cpp

-include $(DEBUDA_STUB_DEPS)

$(DEBUDA_STUB_TARGET): $(DEBUDA_STUB_OBJS)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DEBUDA_STUB_INCLUDES) -o $@ $^ $(LDFLAGS) $(DEBUDA_STUB_LDFLAGS)
	$(PRINT_OK)

.PHONY: dbd/debuda-stub
dbd/debuda-stub: $(DEBUDA_STUB_TARGET)
	$(PRINT_OK)

dbd/debuda-stub/clean:
	-rm $(DEBUDA_STUB_TARGET) $(SILENT_ERRORS)