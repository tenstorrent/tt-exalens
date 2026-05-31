CONFIG ?= Debug
DUMP_ELFS ?= OFF
# build_debug or build_release
BUILD_DIR ?= build_$(shell echo $(CONFIG) | tr '[:upper:]' '[:lower:]')

.PHONY: build
build:
	@if which ccache > /dev/null; then \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DCMAKE_C_COMPILER_LAUNCHER=ccache \
			-DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
			-DCMAKE_BUILD_TYPE=$(CONFIG) \
			-DDUMP_ELFS=$(DUMP_ELFS) \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	else \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DCMAKE_BUILD_TYPE=$(CONFIG) \
			-DDUMP_ELFS=$(DUMP_ELFS) \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	fi
	@ninja -C $(BUILD_DIR)

.PHONY: debug
debug: CONFIG=Debug
debug: build

.PHONY: release
release: CONFIG=Release
release: build

dump_elfs:
	DUMP_ELFS=ON $(MAKE) build

.PHONY: clean
clean:
	@rm -rf build build_debug build_release build_riscv build_wheel compile_commands.json

.PHONY: test
test:
	@echo "Installing dependencies"
	TTEXALENS_INSTALL=true TEST_INSTALL=true $(TTEXALENS_HOME)/scripts/install-deps.sh

	@echo "Running tests"
	./test/run_all.sh

.PHONY: mypy
mypy:
	@echo "Running mypy"
	python3 -m mypy

.PHONY: pyright
pyright:
	@echo "Running basedpyright"
	python3 -m basedpyright

.PHONY: wheel
wheel:
	pip wheel --no-deps --no-cache-dir . --wheel-dir build_wheel

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
