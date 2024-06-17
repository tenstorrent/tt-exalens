# Every variable in subdir must be prefixed with subdir (emulating a namespace)
DEBUDA_SERVER_SRCS = $(wildcard dbd/server/app/*.cpp)
DEBUDA_SERVER = $(BINDIR)/debuda-server-standalone

# Libraries this target depends on
DEBUDA_SERVER_LINK_DEPS = $(DEBUDA_SERVER_LIB) $(BACKEND_LIB)
# Also add those libraries as with shared name to avoid hardcoding library paths.
DEBUDA_SERVER_LIB_DEPS = -ldbdserver -ldevice -lstdc++fs

DEBUDA_SERVER_OBJS = $(addprefix $(OBJDIR)/, $(DEBUDA_SERVER_SRCS:.cpp=.o))
DEBUDA_SERVER_DEPS = $(addprefix $(OBJDIR)/, $(DEBUDA_SERVER_SRCS:.cpp=.d))

# TODO: Remove budabackend dependencies
DEBUDA_SERVER_INCLUDES = \
	$(BASE_INCLUDES) \
	-I$(DEBUDA_HOME)/third_party/umd \
	-Idbd/server/lib/inc \

DEBUDA_SERVER_LDFLAGS =  $(DEBUDA_SERVER_LIB_DEPS) -lyaml-cpp -lzmq -Wl,-rpath,\$$ORIGIN/../lib:\$$ORIGIN -pthread

-include $(DEBUDA_SERVER_DEPS)

dbd/server/app: $(DEBUDA_SERVER)

$(DEBUDA_SERVER): $(DEBUDA_SERVER_OBJS) $(DEBUDA_SERVER_LINK_DEPS) $(UMD_DEVICE_LIB) $(DEBUDA_SERVER_LIB)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DEBUDA_SERVER_LIB_DEPS) -o $@ $^ $(LDFLAGS) $(DEBUDA_SERVER_LDFLAGS)

.PRECIOUS: $(OBJDIR)/dbd/server/app/%.o
$(OBJDIR)/dbd/server/app/%.o: dbd/server/app/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DEBUDA_SERVER_INCLUDES) $(DEBUDA_SERVER_DEFINES) -c -o $@ $<
