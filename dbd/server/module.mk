dbd/server: dbd/server/app dbd/server/lib

ifndef DEBUDA_SERVER_LIB_SRCS
  include $(DEBUDA_HOME)/dbd/server/lib/module.mk
endif
include $(DEBUDA_HOME)/dbd/server/unit_tests/module.mk
include $(DEBUDA_HOME)/dbd/server/app/module.mk
