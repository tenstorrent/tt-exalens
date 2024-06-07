.SUFFIXES:

# Setup CONFIG, DEVICE_RUNNER, and out/build dirs first
DEBUGGER_HOME ?= $(shell git rev-parse --show-toplevel)
CONFIG ?= develop
ARCH_NAME ?= grayskull
HOST_ARCH = $(shell uname -m)

OUT ?= $(DEBUGGER_HOME)/build
PREFIX ?= $(OUT)
TT_MODULES ?= 

CONFIG_CFLAGS =
CONFIG_LDFLAGS =
OPT_LEVEL=
DEBUG_FLAGS=
UMD_VERSIM_STUB ?= 1


GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
GIT_HASH = $(shell git describe --always --dirty)

ifeq ($(CONFIG), release)
OPT_LEVEL = -O3 -fno-lto
else ifeq ($(CONFIG), develop)
OPT_LEVEL = -O3 -fno-lto
DEBUG_FLAGS += -DTT_DEBUG_LOGGING
else ifeq ($(CONFIG), ci)	# significantly smaller artifacts
OPT_LEVEL = -O3
DEBUG_FLAGS += -DTT_DEBUG -DTT_DEBUG_LOGGING
else ifeq ($(CONFIG), assert)
OPT_LEVEL = -O3 -g
DEBUG_FLAGS += -DTT_DEBUG -DTT_DEBUG_LOGGING
else ifeq ($(CONFIG), asan)
OPT_LEVEL = -O3 -g
DEBUG_FLAGS += -DTT_DEBUG -DTT_DEBUG_LOGGING -fsanitize=address
CONFIG_LDFLAGS += -fsanitize=address
else ifeq ($(CONFIG), ubsan)
OPT_LEVEL = -O3 -g
DEBUG_FLAGS += -DTT_DEBUG -DTT_DEBUG_LOGGING -fsanitize=undefined
CONFIG_LDFLAGS += -fsanitize=undefined
else ifeq ($(CONFIG), debug)
OPT_LEVEL = -O0 -g
DEBUG_FLAGS += -DDEBUG -DTT_DEBUG -DTT_DEBUG_LOGGING
else
$(error Unknown value for CONFIG "$(CONFIG)")
endif

ENABLE_CODE_TIMERS ?= 1

ifeq ($(ENABLE_CODE_TIMERS), 1)
DEBUG_FLAGS += -DTT_ENABLE_CODE_TIMERS
endif

# ifeq ($(BACKEND_PROFILER_DEBUG), 1)
# DEBUG_FLAGS += -DBACKEND_PROFILER_DEBUG
# endif

CONFIG_CFLAGS += $(OPT_LEVEL)
CONFIG_CFLAGS += $(DEBUG_FLAGS)

OBJDIR = $(OUT)/obj
LIBDIR = $(OUT)/lib
BINDIR = $(OUT)/bin
INCDIR = $(OUT)/include
TESTDIR = $(OUT)/test
UTSDIR = $(OUT)/unit_tests
DOCSDIR = $(OUT)/docs

# Top level flags, compiler, defines etc.

CCACHE := $(shell command -v ccache 2> /dev/null)

# Ccache setup
ifneq ($(CCACHE),)
	export CCACHE_DIR=$(HOME)/.ccache
	export CCACHE_MAXSIZE=10
	export CCACHE_UMASK=002
	export CCACHE_COMPRESS=true
	export CCACHE_NOHARDLINK=true
	export CCACHE_DIR_EXISTS=$(shell [ -d $(CCACHE_DIR) ] && echo "1")
	ifneq ($(CCACHE_DIR_EXISTS), 1)
	  $(info $(HOME)/.ccache directory does not exist, creating it.")
	  $(shell mkdir -p $(CCACHE_DIR))
	endif
	#CCACHE_CMD=$(CCACHE)
	#$(info CCACHE IS ENABLED)
#else
	#$(warning "ccache is not installed, please reach out to devops if it's expected.")
	#$(info CCACHE IS DISABLED)
endif

#WARNINGS ?= -Wall -Wextra
WARNINGS ?= -Wdelete-non-virtual-dtor -Wreturn-type -Wswitch -Wuninitialized -Wno-unused-parameter
CC ?= $(CCACHE_CMD) gcc
CXX ?= $(CCACHE_CMD) g++
DEVICE_CXX = g++
# fmt is included from UMD
ifeq ("$(HOST_ARCH)", "aarch64")
CFLAGS ?= -MMD $(WARNINGS) -I. $(CONFIG_CFLAGS) -DBUILD_DIR=\"$(OUT)\" -DFMT_HEADER_ONLY -Ithird_party/umd/third_party/fmt/include
else
# Add AVX and FMA (Fused Multiply Add) flags for x86 compile
CFLAGS ?= -MMD $(WARNINGS) -I. $(CONFIG_CFLAGS) -mavx2 -mfma -DBUILD_DIR=\"$(OUT)\" -DFMT_HEADER_ONLY -Ithird_party/umd/third_party/fmt/include
endif
CXXFLAGS ?= --std=c++17 -fvisibility-inlines-hidden
LDFLAGS ?= $(CONFIG_LDFLAGS) -Wl,-rpath,$(PREFIX)/lib -L$(LIBDIR) -ldl
SHARED_LIB_FLAGS = -shared -fPIC
STATIC_LIB_FLAGS = -fPIC

COREMODEL_SPARTA_LIBS = -lyaml-cpp -lpthread -lboost_fiber -lboost_date_time -lboost_filesystem -lboost_iostreams -lboost_serialization -lboost_timer -lboost_program_options
ifeq ($(findstring clang,$(CC)),clang)
WARNINGS += -Wno-c++11-narrowing -Wno-unused-command-line-argument
LDFLAGS += -lstdc++
else
WARNINGS += -Wmaybe-uninitialized
LDFLAGS += -lstdc++
endif

UMD_HOME = third_party/umd
UMD_USER_ROOT = $(DEBUGGER_HOME)

# TODO: Check if needed
PYTHON_VERSION ?= python3.8

# TODO: Check what else to build
build: gitinfo umd
	$(MAKE) dbd

#TODO: Set up unit test build.
#TODO: Set up valgrind.

umd: umd_device

# TODO: Set clean properly.
clean: clean_umd_device 
	rm -rf $(OUT)

install: build
ifeq ($(PREFIX), $(OUT))
	@echo "To install you must set PREFIX, e.g."
	@echo ""
	@echo "	PREFIX=/usr CONFIG=release make install"
	@echo ""
	@exit 1
endif
	cp -r $(LIBDIR)/* $(PREFIX)/lib/
	cp -r $(INCDIR)/* $(PREFIX)/include/
	cp -r $(BINDIR)/* $(PREFIX)/bin/

gitinfo:
	mkdir -p $(OUT)
# Initialization steps for building + running the Zebu emulator device
	rm -f $(OUT)/.gitinfo
	@echo $(GIT_BRANCH) >> $(OUT)/.gitinfo
	@echo $(GIT_HASH) >> $(OUT)/.gitinfo

include third_party/umd/device/module.mk

include dbd/module.mk
