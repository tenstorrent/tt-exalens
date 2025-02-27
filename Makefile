CONFIG ?= Debug
JTAG ?= OFF

.PHONY: build
build:
	@echo "Building"
	@if [ ! -f build/build.ninja ] || ! grep -iq "CMAKE_BUILD_TYPE:STRING=$(CONFIG)" build/CMakeCache.txt; then \
		if which ccache > /dev/null; then \
			cmake -B build -G Ninja -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=$(CONFIG) -DDOWNLOAD_TTEXALENS_PRIVATE=$(JTAG); \
		else \
			cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=$(CONFIG) -DDOWNLOAD_TTEXALENS_PRIVATE=$(JTAG); \
		fi \
	fi
	@ninja -C build

.PHONY: clean
clean:
	@rm -rf build/

.PHONY: test
test:
	@echo "Installing dependencies"
	TTEXALENS_INSTALL=true TEST_INSTALL=true $(TTEXALENS_HOME)/scripts/install-deps.sh

	@echo "Running tests"
	./test/run_all.sh

.PHONY: wheel_develop
wheel_develop:
	CONFIG=Debug python3 setup.py bdist_wheel -d build/ttexalens_wheel

.PHONY: wheel
wheel:
	STRIP_SYMBOLS=1 CONFIG=Release python3 setup.py bdist_wheel -d build/ttexalens_wheel

.PHONY: ttexalens_server_unit_tests_run_only
ttexalens_server_unit_tests_run_only:
	@echo "Running: build/bin/ttexalens_server_unit_tests"
	@build/bin/ttexalens_server_unit_tests

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
