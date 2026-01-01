BUILD_DIR ?= build

.PHONY: build
build:
	@if which ccache > /dev/null; then \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DCMAKE_C_COMPILER_LAUNCHER=ccache \
			-DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	else \
		cmake -B $(BUILD_DIR) -G Ninja \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5; \
	fi
	@ninja -C $(BUILD_DIR)

.PHONY: clean
clean:
	@rm -rf build build_riscv

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

.PHONY: wheel
wheel:
	pip wheel --no-deps --no-cache-dir --extra-index-url https://test.pypi.org/simple/ . --wheel-dir build/ttexalens_wheel

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
