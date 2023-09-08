include $(BUDA_HOME)/infra/common.mk

# Every variable in subdir must be prefixed with subdir(emulating a namespace)

DBD_INCLUDES = $(BASE_INCLUDES) $(GOLDEN_INCLUDES) $(MODEL2_INCLUDES) $(NETLIST_INCLUDES) $(MODEL_INCLUDES) -Iverif/directed_tests -Iverif -Ithird_party/json
DBD_LIB = $(LIBDIR)/libdbd.a
DBD_DEFINES = -DGIT_HASH=$(shell git rev-parse HEAD)
DBD_INCLUDES += -Imodel -Inetlist -Icommon -I$(YAML_PATH) -Isrc/firmware/riscv/$(ARCH_NAME)/
DBD_CFLAGS = $(CFLAGS) -Werror
DBD_LDFLAGS = -ltt -ldevice -lstdc++fs -lpthread -lyaml-cpp -lcommon -lhwloc -lboost_program_options

DBD_SRCS = $(wildcard dbd/*.cpp)

DBD_OBJS = $(addprefix $(OBJDIR)/, $(DBD_SRCS:.cpp=.o))
DBD_DEPS = $(addprefix $(OBJDIR)/, $(DBD_SRCS:.cpp=.d))

-include $(DBD_DEPS)

# Main target: it builds the standalone server executable
dbd: verif/netlist_tests/debuda-server-standalone
	$(PRINT_TARGET)
	$(PRINT_OK)

dbd/clean: dbd/tools/clean
	-rm $(BINDIR)/dbd_* $(SILENT_ERRORS)
	-rm $(OBJDIR)/dbd/* $(SILENT_ERRORS)

$(DBD_LIB): $(DBD_OBJS) $(BACKEND_LIB)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	ar rcs -o $@ $(DBD_OBJS)
	$(PRINT_OK)

$(BINDIR)/dbd_%: $(OBJDIR)/dbd/%.o $(BACKEND_LIB) $(DBD_LIB) $(VERIF_LIB)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DBD_INCLUDES) -o $@ $^ $(LDFLAGS) $(DBD_LDFLAGS)
	$(PRINT_OK)

$(OBJDIR)/dbd/%.o: dbd/%.cpp
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(DBD_CFLAGS) $(CXXFLAGS) $(STATIC_LIB_FLAGS) $(DBD_INCLUDES) $(DBD_DEFINES) -c -o $@ $<
	$(PRINT_OK)

include $(BUDA_HOME)/dbd/tools/module.mk