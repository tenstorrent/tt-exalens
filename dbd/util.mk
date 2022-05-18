# Include this file in your makefile by copying the following lines
# ROOT?=$(shell git rev-parse --show-toplevel)
# include $(ROOT)/dbd/common.mk

# Make sure we don't print what is executed. If you want the echoing, run make with SILENT=0
ifneq ($(SILENT),0)
.SILENT:
endif

# QP - 'quiet piping' - to be used at the end of commands that print lots of stuff
QP ?= > /dev/null

# Q - 'quiet' - te be used at the beggining of a command, if you want to suppress the printout 
#               of the command itself. Set Q=@ to make everything quiet.
Q ?= 

# Color related stuff
# source: http://vmrob.com/colorized-makefiles/
#
# Set colors
RED    =\033[0;31m
GREEN  =\033[0;32m
YELLOW =\033[0;33m
BLUE   =\033[0;34m
NC     =\033[0m

TITLE    =\033[7;34m
SUBTITLE =\033[1;34m

#NOCOLOR=1

ifndef NOCOLOR
	ERROR_COLOR  =\033[7;31m
	WARN_COLOR   =\033[7;33m
	SUCCESS_COLOR=\033[7;32m
endif

OK_STRING=$(SUCCESS_COLOR)[OK]$(NC)
ERROR_STRING=$(ERROR_COLOR)[ERROR]$(NC)
WARN_STRING=$(WARN_COLOR)[WARNING]$(NC)
SUCCESS_STRING=$(SUCCESS_COLOR)[SUCCESS]$(NC)

PRETTY_2_COL = awk '{ printf "%-50s %-10s\n",$$1, $$2; }'
PRINT_ERROR   =  printf "$@ $(ERROR_STRING)\n"   | $(PRETTY_2_COL) && printf "$(CMD)\n$$LOG\n" && false
PRINT_WARNING =  printf "$@ $(WARN_STRING)\n"    | $(PRETTY_2_COL) && printf "$(CMD)\n$$LOG\n"
PRINT_OK      =  printf "$@ $(OK_STRING)\n"      | $(PRETTY_2_COL)
PRINT_SUCCESS =  printf "$@ $(SUCCESS_STRING)\n" | $(PRETTY_2_COL)
PRINT_TARGET  =  printf "${TITLE}$@${NC}\n"

SILENT_ERRORS := 2> /dev/null ||: # Hide stderr and don't report errors to make.

# Some magic to get directories
THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
CALLER_MAKEFILE_LIST := $(filter-out $(THIS_MAKEFILE),$(MAKEFILE_LIST))
MAKEFILE_PATH := $(abspath $(lastword $(CALLER_MAKEFILE_LIST)))
CURRENT_DIR := $(notdir $(patsubst %/,%,$(dir $(MAKEFILE_PATH))))
