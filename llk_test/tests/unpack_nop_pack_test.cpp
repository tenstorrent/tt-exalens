#include <cstdint>

#include "llk_defs.h"
#include "ckernel.h"

// Globals
uint32_t unp_cfg_context = 0;
uint32_t pack_sync_tile_dst_ptr = 0;
volatile uint32_t tt_l1_ptr l1_buffer[16] __attribute__ ((section (".text#"))) __attribute__ ((aligned (16)));

extern "C" void wzerorange(uint32_t *start, uint32_t *end)
{
    for (; start != end; start++)
    {
        *start = 0;
    }
}

#ifdef LLK_TRISC_UNPACK

#include "llk_unpack_A.h"
#include "llk_unpack_common.h"

__attribute__((section(".init"))) uint32_t buffer[16 * 16 * 4];

void run_kernel()
{
    for(int i = 0; i < 16*16*4; i++)
    {
        buffer[i] = i | 0xF0000000;
    }
    // run_kernel
        // setup_kernel

        // hlk_process_all_inputs
            // hlk_setup_kernel
                // hlk_hw_config_single_operand
                    // llk_unpack_A_hw_configure_disaggregated
                        // llk_unpack_A_hw_configure
                            // _llk_unpack_A_hw_configure_
                            _llk_unpack_A_hw_configure_((uint32_t)DataFormat::Int32, (uint32_t)DataFormat::Int32);
                            (*((volatile uint32_t*)0xd004)) = 0x4421;

                // hlk_copy_tile_to_dst_init
                    // hlk_copy_tile_to_dst_init_short
                        // llk_unpack_A_init
                            // _llk_unpack_A_init_
                            _llk_unpack_A_init_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>(0, 0, FACE_R_DIM, 4, (uint32_t)DataFormat::Int32, (uint32_t)DataFormat::Int32);
                            (*((volatile uint32_t*)0xd004)) = 0x4441;

            // hlk_pre_input_processing

            // hlk_process_single_input
                // hlk_copy_tile_to_dst
                    // llk_unpack_A
                        // _llk_unpack_A_
                        _llk_unpack_A_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>((((uint32_t)&buffer)/16)-1, 0, (uint32_t)DataFormat::Int32, (uint32_t)DataFormat::Int32);
                        (*((volatile uint32_t*)0xd004)) = 0x4444;

            // hlk_post_input_processing

}

#endif

#ifdef LLK_TRISC_MATH

#include "llk_math_eltwise_unary_datacopy.h"

void run_kernel()
{
    _llk_math_eltwise_unary_datacopy_<DataCopyType::A2D, BroadcastType::NONE, DstSync::SyncFull, false, true>(0, (uint32_t)DataFormat::Int32, (uint32_t)DataFormat::Int32);
    set_math_semaphores();
}

#endif

#ifdef LLK_TRISC_PACK

#include "llk_pack.h"
#include "llk_pack_common.h"

volatile __attribute__((section(".init"))) uint32_t buffer1[16 * 16 * 4];

void run_kernel()
{
    for(int i = 0; i < 16*16*4; i++)
    {
        buffer1[i] = 0x4321;
    }
    _llk_pack_hw_configure_((uint32_t)DataFormat::Int32, (uint32_t)DataFormat::Int32, 16*16*4);
    _llk_pack_init_<false, false, DstTileFaceLayout::RowMajor, false>((uint32_t)DataFormat::Int32);
    _llk_pack_dest_init_<DstSync::SyncFull, DstTileFaceLayout::RowMajor, false, false>();
    _llk_packer_wait_for_math_done_();
    _llk_pack_(0, (((uint32_t)&buffer1)/16)-1);
}

#endif
