#include <cstdint>
#include <cstdio>

#include "llk_defs.h"
#include "ckernel.h"

// Globals
uint32_t unp_cfg_context = 0;
uint32_t pack_sync_tile_dst_ptr = 0;
volatile uint32_t tt_l1_ptr l1_buffer[16] __attribute__ ((section (".text#"))) __attribute__ ((aligned (16)));

#ifdef LLK_TRISC_UNPACK

#include "../helpers/unpack_kernels.h"

void run_kernel(){
    for(int i = 0; i < KERN_CNT; i++) {
        if (kernels[i]) {
            kernels[i]();     
        } else{
            // WRITE SOMETHING DIFFERENT FROM 1 TO MAILBOX
        }
    }
}

#endif

#ifdef LLK_TRISC_MATH

#include "../helpers/math_kernels.h"

void run_kernel(){
    for(int i = 0; i < KERN_CNT; i++) {
        if (kernels[i]) {
            kernels[i]();     
        } else{
            // WRITE SOMETHING DIFFERENT FROM 1 TO MAILBOX
        }
    }
}

#endif

#ifdef LLK_TRISC_PACK

#include "../helpers/pack_kernels.h"

void run_kernel(){
    for(int i = 0; i < KERN_CNT; i++) {
        if (kernels[i]) {
            kernels[i]();     
        } else{
            // WRITE SOMETHING DIFFERENT FROM 1 TO MAILBOX
        }
    }
}

#endif

#endif