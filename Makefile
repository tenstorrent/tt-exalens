BUILD_DIR ?= build
DUMP_ELFS ?= OFF

.PHONY: build
build:
	@if which ccache > /dev/null; then \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DCMAKE_C_COMPILER_LAUNCHER=ccache \
			-DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
			-DDUMP_ELFS=$(DUMP_ELFS) \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	else \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DDUMP_ELFS=$(DUMP_ELFS) \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	fi
	@ninja -C $(BUILD_DIR)

dump_elfs:
	DUMP_ELFS=ON $(MAKE) build

.PHONY: clean
clean:
	@rm -rf build

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

.PHONY: wheel
wheel:
	pip wheel --no-deps --no-cache-dir . --wheel-dir build/ttexalens_wheel

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
