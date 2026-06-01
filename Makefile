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
	@echo "Running mypy"
	python3 -m mypy
	@echo "Running basedpyright"
	python3 -m basedpyright

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

# AddressSanitizer build. Rebuilds the native `_native_ttexalens` extension
# with -fsanitize=address; run tests with:
#   LD_PRELOAD=$$(gcc -print-file-name=libasan.so) \
#   ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1 \
#   python3 -X faulthandler -m unittest <selector>
# Forces a fresh configure into build_asan/ so the regular dev tree (build,
# build_debug) is unaffected.
.PHONY: asan
asan:
	@cmake -B build_asan -G Ninja \
		-DCMAKE_BUILD_TYPE=Debug \
		-DCMAKE_C_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" \
		-DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g" \
		-DCMAKE_LINKER_FLAGS="-fsanitize=address" \
		-DCMAKE_SHARED_LINKER_FLAGS="-fsanitize=address" \
		-DCMAKE_POLICY_VERSION_MINIMUM=3.5
	@LD_PRELOAD=$$(gcc -print-file-name=libasan.so) \
		ASAN_OPTIONS=detect_leaks=0 \
		ninja -C build_asan

TTEXALENS_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
