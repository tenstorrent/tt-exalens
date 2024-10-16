
/*
===================================
All constants are defined in file ../helper/params.h
and are set during compilation.

DATA_FORMAT -> used insinde UNPACK and PACK
ELTWISE_BINARY_OP -> used inside of MATH for binary eltwise kernels 

===================================
*/

#include <cstdint>
#include <cstdio>

#include "llk_defs.h"
#include "ckernel.h"

// Globals
uint32_t unp_cfg_context = 0;
uint32_t pack_sync_tile_dst_ptr = 0;
volatile uint32_t tt_l1_ptr l1_buffer[16] __attribute__ ((section (".text#"))) __attribute__ ((aligned (16)));

#ifdef LLK_TRISC_UNPACK

#include "llk_unpack_AB.h"
#include "llk_unpack_common.h"
#include "../helpers/params.h"

volatile uint32_t* buffer_A = (volatile uint32_t*)0x1b000;
volatile uint32_t* buffer_B = (volatile uint32_t*)0x1c000;

void run_kernel()
{
    _llk_unpack_AB_hw_configure_(DATA_FORMAT, DATA_FORMAT, DATA_FORMAT, DATA_FORMAT);
    _llk_unpack_AB_init_<>();
    _llk_unpack_AB_<>((std::uint32_t)buffer_A/16-1,(std::uint32_t)buffer_B/16-1);
}

#endif

#ifdef LLK_TRISC_MATH

#include "llk_math_eltwise_binary.h"
#include "../helpers/params.h"

void run_kernel()
{
    _llk_math_eltwise_binary_init_<ELTWISE_BINARY_OP, BroadcastType::NONE>(4, 0, 0);
    _llk_math_eltwise_binary_<ELTWISE_BINARY_OP, BroadcastType::NONE>(4, 0, true);
    set_math_semaphores();
}

#endif 

#ifdef LLK_TRISC_PACK

#include "llk_pack.h"
#include "llk_pack_common.h"
#include "../helpers/params.h"

//__attribute__((section(".text"))) uint32_t buffer_Dest[16 * 16 * 4];
volatile uint32_t* buffer_Dest = (volatile uint32_t*)0x1a000;
void run_kernel()
{
    _llk_pack_hw_configure_(DATA_FORMAT, DATA_FORMAT, 16*16*4);
    _llk_pack_init_<false, false, DstTileFaceLayout::RowMajor, false>(DATA_FORMAT);
    _llk_pack_dest_init_<DstSync::SyncFull, DstTileFaceLayout::RowMajor, false, false>();
    _llk_packer_wait_for_math_done_();
    _llk_pack_(0, (std::uint32_t)buffer_Dest/16-1);
}

#endif