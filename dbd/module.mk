include infra/common.mk

DBD_OUT?=$(OUT)/dbd

# Main target: it builds the standalone server executable, and pybind modules
dbd: dbd/server dbd/pybind dbd/riscv
	$(PRINT_TARGET)
	$(PRINT_OK)

# Tests target: it builds everything and tests and run tests
dbdtests: dbd dbd/server/unit_tests dbd/pybind/unit_tests

# MARKDOWN_FILES=
MARKDOWN_FILES=debuda-py-intro.md
MARKDOWN_FILES+=debuda-py-tutorial.md
MARKDOWN_FILES+=$(DBD_OUT)/debuda-commands-help.md

# TODO: This needs to be resolved properly (see issue #54)
# .PHONY: dbd/release
# dbd/release: dbd dbd/documentation
# 	echo "The board should be reset before running this target."
# 	echo "Full command: unset CONFIG ; make clean ; make dbd/documentation ; make dbd/release."
# 	dbd/bin/package.sh $(DBD_OUT)

dbd/clean: dbd/tools/clean
	-rm $(BINDIR)/dbd_* $(SILENT_ERRORS)
	-rm $(OBJDIR)/dbd/* $(SILENT_ERRORS)

.PHONY: dbd/test
DBD_VENV=$(DBD_OUT)/dbd-venv
dbd/test:
	echo "Create a clean python environment: $(DBD_VENV)"
	-rm -rf $(DBD_VENV)
	python3 -m venv $(DBD_VENV)
	echo "Activate, install requirements and run tests"
	. $(DBD_VENV)/bin/activate && pip install -r dbd/requirements.txt && dbd/tests/test-debuda-py.sh

.PHONY: dbd/coverage
dbd/coverage:
	COV=1 $(MAKE) dbd/test
	COV=1 $(MAKE) dbd/documentation
	coverage report --sort=cover
	coverage lcov # generates coverage data in the format expected by VS code "Code Coverage" extension

.PHONY: dbd/test-elf-parser
dbd/test-elf-parser:
	python3 dbd/test_parse_elf.py
	python3 dbd/test_firmware.py

$(DBD_LIB): $(DBD_OBJS)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	ar rcs -o $@ $(DBD_OBJS)
	$(PRINT_OK)

$(BINDIR)/dbd_%: $(OBJDIR)/dbd/%.o $(DBD_LIB) $(VERIF_LIB)
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CXXFLAGS) $(DBD_INCLUDES) -o $@ $^ $(LDFLAGS) $(DBD_LDFLAGS)
	$(PRINT_OK)

$(OBJDIR)/dbd/%.o: dbd/%.cpp
	$(PRINT_TARGET)
	@mkdir -p $(@D)
	$(CXX) $(DBD_CFLAGS) $(CXXFLAGS) $(STATIC_LIB_FLAGS) $(DBD_INCLUDES) $(DBD_DEFINES) -c -o $@ $<
	$(PRINT_OK)

include $(DEBUDA_HOME)/dbd/server/module.mk
include $(DEBUDA_HOME)/dbd/pybind/module.mk
