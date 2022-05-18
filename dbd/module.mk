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

-include $(DBD_DEPS)

# Each module has a top level target as the entrypoint which must match the subdir name
dbd: $(OUT)/bin/dbd_modify_netlist
	$(PRINT_OK)

dbd_clean:
	-rm $(OUT)/bin/dbd_* $(SILENT_ERRORS)

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

