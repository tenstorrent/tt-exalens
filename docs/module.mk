include infra/common.mk

DOC_DIR?=$(TTLENS_HOME)/docs

.PHONY: docs
docs: build
	@echo "${YELLOW}Generating documentation${NC}"
	@echo "${YELLOW}Using the output directory $(DOC_DIR)${NC}"

	echo "Generating library documentation..."
	python -m docs.bin.generate-lib-docs $(TTLENS_HOME)/ttlens $(DOC_DIR)/ttlens-lib-docs.md
	$(PRINT_OK)

	echo "Generating application documentation..."
	python -m docs.bin.generate-command-docs $(TTLENS_HOME)/ttlens/ttlens_commands $(DOC_DIR)/ttlens-app-docs.md
	$(PRINT_OK)

.PHONY: clean-docs
clean-docs:
	@echo "${YELLOW}Cleaning documentation${NC}"
	rm -rf $(DOC_DIR)/ttlens-lib-docs.md
	rm -rf $(DOC_DIR)/ttlens-app-docs.md
	$(PRINT_OK)
