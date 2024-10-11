#include <cstdint>
#include <cstdio>

#include "llk_defs.h"
#include "ckernel.h"
#include "../helpers/args.h"

// Globals
uint32_t unp_cfg_context = 0;
uint32_t pack_sync_tile_dst_ptr = 0;
volatile uint32_t tt_l1_ptr l1_buffer[16] __attribute__ ((section (".text#"))) __attribute__ ((aligned (16)));


#ifdef LLK_TRISC_UNPACK

#include "llk_unpack_AB_matmul.h"
#include "llk_unpack_common.h"

__attribute__((section(".trisc0_data"))) uint32_t buffer_A[16 * 16 * 4]; // this buffer is filled with data from _test.py
__attribute__((section(".trisc0_data"))) uint32_t buffer_B[16 * 16 * 4]; // this buffer is filled with data from _test.py

void run_kernel()
{
    for(int i = 0; i < 16*16*4; i++)
    {
        buffer_A[i] = 0x4040;
        buffer_B[i] = 0x4040;
    }
    (*((volatile uint32_t*)0xd004)) = 0xAAAAAAAA;
    _llk_unpack_AB_matmul_hw_configure_((uint32_t)DataFormat::Float16_b, (uint32_t)DataFormat::Float16_b, (uint32_t)DataFormat::Float16_b, (uint32_t)DataFormat::Float16_b);
    _llk_unpack_AB_matmul_init_<>();
    _llk_unpack_AB_matmul_<>((((uint32_t)&buffer_A)/16)-1,(((uint32_t)&buffer_B)/16)-1,0,0,1,1);
}

#endif

#ifdef LLK_TRISC_MATH

//#include "llk_math_eltwise_binary.h"
#include "llk_math_matmul.h"

void run_kernel()
{
    (*((volatile uint32_t*)0x12004)) = 0xBBBBBBBB;
    _llk_math_matmul_init_<1,DstTileFaceLayout::RowMajor>();
    _llk_math_matmul_<4,DstTileFaceLayout::RowMajor>(0);
    //_llk_math_eltwise_unary_datacopy_<DataCopyType::A2D, BroadcastType::NONE, DstSync::SyncFull, false, false>(0, (uint32_t)DataFormat::Float16_b, (uint32_t)DataFormat::Float16_b);
    //_llk_math_eltwise_binary_init_<EltwiseBinaryType::ELWADD, BroadcastType::NONE>(4, 0, 0);
    //_llk_math_eltwise_binary_<EltwiseBinaryType::ELWADD, BroadcastType::NONE>(4, 0, true);
    set_math_semaphores();
}

#endif

#ifdef LLK_TRISC_PACK

#include "llk_pack.h"
#include "llk_pack_common.h"

volatile __attribute__((section(".text"))) uint32_t buffer_Dest[16 * 16 * 4];

//parametrize data formats

void run_kernel()
{
    for(int i = 0; i < 16*16*4; i++)
    {
        buffer_Dest[i] = 0xaaaabbbb;
    }
    (*((volatile uint32_t*)0x16004)) = 0xCCCCCCCC;
    _llk_pack_hw_configure_((uint32_t)DataFormat::Float16_b, (uint32_t)DataFormat::Float16_b, 16*16*4);
    _llk_pack_init_<false, false, DstTileFaceLayout::RowMajor, false>((uint32_t)DataFormat::Float16_b);
    _llk_pack_dest_init_<DstSync::SyncFull, DstTileFaceLayout::RowMajor, false, false>();
    _llk_packer_wait_for_math_done_();
    _llk_pack_(0, (((uint32_t)&buffer_Dest)/16)-1);
}

#endif