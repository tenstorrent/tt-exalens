INCLUDE "memory.ld"

REGION_ALIAS("REGION_CODE", BRISC_CODE)
REGION_ALIAS("REGION_DATA", BRISC_LOCAL_DATA_MEM)
REGION_ALIAS("REGION_STACK", BRISC_STACK_MEM)
__firmware_stack_size = 1024;
__firmware_start = DEFINED(__fw_export_end_text) ? __fw_export_end_text : ORIGIN(REGION_CODE);
__ldm_start = DEFINED(__fw_export_ldm_end) ? __fw_export_ldm_end : ORIGIN(REGION_DATA);

INCLUDE "sections.ld"
