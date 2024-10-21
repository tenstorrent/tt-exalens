.PHONY: build
build:
	@echo "Building"
	@if [ ! -f build/build.ninja ]; then \
		cmake -B build -G Ninja; \
	fi
	@ninja -C build

.PHONY: clean
clean:
	@rm -rf build/

.PHONY: test
test:
	@echo "Running tests"
	./test/run_all.sh

.PHONY: wheel_develop
wheel_develop:
	python3 setup.py bdist_wheel -d build/debuda_wheel

.PHONY: wheel
wheel:
	STRIP_SYMBOLS=1 python3 setup.py bdist_wheel -d build/debuda_wheel

.PHONY: dbd_server_unit_tests_run_only
dbd_server_unit_tests_run_only:
	@echo "Running: build/bin/debuda_server_unit_tests"
	@build/bin/debuda_server_unit_tests

DEBUDA_HOME ?= $(shell git rev-parse --show-toplevel)

include docs/module.mk
