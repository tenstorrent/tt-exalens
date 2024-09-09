include infra/common.mk

DOC_DIR?=$(DEBUDA_HOME)/docs

.PHONY: docs
docs: build
	@echo "${YELLOW}Generating documentation${NC}"
	@echo "${YELLOW}Using the output directory $(DOC_DIR)${NC}"	
	
	echo "Generating library documentation..."
	python -m docs.bin.generate-lib-docs $(DEBUDA_HOME)/dbd $(DOC_DIR)/debuda-lib-docs.md
	$(PRINT_OK)

	echo "Generating application documentation..."
	python -m docs.bin.generate-command-docs $(DEBUDA_HOME)/dbd/debuda_commands $(DOC_DIR)/debuda-app-docs.md
	$(PRINT_OK)

.PHONY: clean-docs
clean-docs:
	@echo "${YELLOW}Cleaning documentation${NC}"
	rm -rf $(DOC_DIR)/debuda-lib-docs.md
	rm -rf $(DOC_DIR)/debuda-app-docs.md
	$(PRINT_OK)
