CONFIG ?= Debug
JTAG ?= OFF
BUILD_DIR ?= build_$(shell echo $(CONFIG) | tr '[:upper:]' '[:lower:]') # build_debug or build_release

.PHONY: build
build:
	@echo "Building"
	@if [ ! -f $(BUILD_DIR)/build.ninja ] || ! grep -iq "CMAKE_BUILD_TYPE:STRING=$(CONFIG)" $(BUILD_DIR)/CMakeCache.txt; then \
		if which ccache > /dev/null; then \
			cmake -B $(BUILD_DIR) -G Ninja -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=$(CONFIG) -DDOWNLOAD_TTEXALENS_PRIVATE=$(JTAG) -DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
		else \
			cmake -B $(BUILD_DIR) -G Ninja -DCMAKE_BUILD_TYPE=$(CONFIG) -DDOWNLOAD_TTEXALENS_PRIVATE=$(JTAG) -DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
		fi \
	fi
	@ninja -C $(BUILD_DIR)

.PHONY: debug
debug: CONFIG=Debug
debug: build

.PHONY: release
release: CONFIG=Release
release: build

.PHONY: clean
clean:
	@rm -rf build build_debug build_release build_elfs

.PHONY: test
test:
	@echo "Installing dependencies"
	TTEXALENS_INSTALL=true TEST_INSTALL=true $(TTEXALENS_HOME)/scripts/install-deps.sh

	@echo "Running tests"
	./test/run_all.sh

.PHONY: mypy
mypy:
	@echo "Running mypy"
	python3 -m mypy -p ttexalens

.PHONY: wheel_develop
wheel_develop:
	CONFIG=Debug pip wheel --no-deps --no-cache-dir . --wheel-dir build/ttexalens_wheel

.PHONY: wheel
wheel:
	STRIP_SYMBOLS=1 CONFIG=Release pip wheel --no-deps --no-cache-dir . --wheel-dir build_release/ttexalens_wheel

.PHONY: ttexalens_server_unit_tests_run_only
ttexalens_server_unit_tests_run_only:
	@echo "Running: build/bin/ttexalens_server_unit_tests"
	@build/bin/ttexalens_server_unit_tests

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
