CONFIG ?= Debug

.PHONY: build
build:
	@echo "Building"
	@if [ ! -f build/build.ninja ] || ! grep -iq "CMAKE_BUILD_TYPE:STRING=$(CONFIG)" build/CMakeCache.txt; then \
		if which ccache > /dev/null; then \
			cmake -B build -G Ninja -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=$(CONFIG); \
		else \
			cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=$(CONFIG); \
		fi \
	fi
	@ninja -C build

.PHONY: clean
clean:
	@rm -rf build/

.PHONY: test
test:
	@echo "Installing dependencies"
	TTLENS_INSTALL=true TEST_INSTALL=true $(TTLENS_HOME)/scripts/install-deps.sh

	@echo "Running tests"
	./test/run_all.sh

.PHONY: wheel_develop
wheel_develop:
	CONFIG=Debug python3 setup.py bdist_wheel -d build/ttlens_wheel

.PHONY: wheel
wheel:
	STRIP_SYMBOLS=1 CONFIG=Release python3 setup.py bdist_wheel -d build/ttlens_wheel

.PHONY: ttlens_server_unit_tests_run_only
ttlens_server_unit_tests_run_only:
	@echo "Running: build/bin/ttlens_server_unit_tests"
	@build/bin/ttlens_server_unit_tests

TTLENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
