DEBUDA_PYBIND_UNIT_TESTS_SRCS  = $(wildcard dbd/pybind/unit_tests/*.cpp)
#TODO: CHECK WHERE TO BUILD THE LIBRARY
DEBUDA_PYBIND_UNIT_TESTS_LIB = $(LIBDIR)/tt_dbd_pybind_unit_tests.so

DEBUDA_PYBIND_UNIT_TESTS_OBJ_DIR  = $(UTSDIR)/dbd/server/obj
DEBUDA_PYBIND_UNIT_TESTS_LIB_OBJS = $(addprefix $(DEBUDA_PYBIND_UNIT_TESTS_OBJ_DIR)/, $(notdir $(DEBUDA_PYBIND_UNIT_TESTS_SRCS:.cpp=.o)))
DEBUDA_PYBIND_UNIT_TESTS_LIB_DEPS = $(addprefix $(DEBUDA_PYBIND_UNIT_TESTS_OBJ_DIR)/, $(notdir $(DEBUDA_PYBIND_UNIT_TESTS_SRCS:.cpp=.d)))

DEBUDA_PYBIND_UNIT_TESTS_LDFLAGS = -lgtest -lgmock -lgtest_main -lzmq -lpthread
DEBUDA_PYBIND_UNIT_TESTS_LDFLAGS += $(LIBDIR)/tt_dbd_pybind.so

.PRECIOUS: $(DEBUDA_PYBIND_UNIT_TESTS_OBJ_DIR)/%.o
$(DEBUDA_PYBIND_UNIT_TESTS_OBJ_DIR)/%.o: dbd/pybind/unit_tests/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(STATIC_LIB_FLAGS) $(DEBUDA_PYBIND_LIB_INCLUDES) -c -o $@ $<

.PHONY: dbd/pybind/unit_tests

$(DEBUDA_PYBIND_UNIT_TESTS_LIB): $(DEBUDA_PYBIND_UNIT_TESTS_LIB_OBJS) $(DEBUDA_PYBIND_LIB)
	@echo "Building: $(DEBUDA_PYBIND_UNIT_TESTS_LIB)"
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(SHARED_LIB_FLAGS) -o $@ $^ $(LDFLAGS) $(DEBUDA_PYBIND_UNIT_TESTS_LDFLAGS)

dbd_pybind_unit_tests_run_only:
	@echo "Running pybind unit tests..."
	@python3 -m unittest dbd/pybind/unit_tests/test_bindings.py

dbd/pybind/unit_tests: $(DEBUDA_PYBIND_UNIT_TESTS_LIB)
ifndef SKIP_UNIT_TESTS_RUN
	@$(MAKE) dbd_pybind_unit_tests_run_only
endif