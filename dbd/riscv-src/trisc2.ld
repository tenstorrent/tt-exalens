INCLUDE "memory.ld"

REGION_ALIAS("REGION_CODE", TRISC2_CODE)
REGION_ALIAS("REGION_DATA", TRISC2_LOCAL_DATA_MEM)
REGION_ALIAS("REGION_STACK", TRISC2_STACK_MEM)
__firmware_stack_size = 768;
__firmware_start = DEFINED(__fw_export_end_text) ? __fw_export_end_text : ORIGIN(REGION_CODE);
__ldm_start = DEFINED(__fw_export_ldm_end) ? __fw_export_ldm_end : ORIGIN(REGION_DATA);

INCLUDE "sections.ld"
