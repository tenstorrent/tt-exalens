#ifndef PACK_KERNELS_HPP
#define PACK_KERNELS_HPP

#ifdef LLK_TRISC_PACK
    
    #include "llk_pack.h"
    #include "llk_pack_common.h"
    #include "helpers.h"

    volatile uint32_t* buffer_Dest = (volatile uint32_t*)0x1a000;
    void(*kernels[KERN_CNT])(void);
    
    void pack_Dest_kernel(){

        _llk_pack_hw_configure_(DATA_FORMAT, DATA_FORMAT, 16*16*4);
        _llk_pack_init_<false, false, DstTileFaceLayout::RowMajor, false>(DATA_FORMAT);
        _llk_pack_dest_init_<DstSync::SyncFull, DstTileFaceLayout::RowMajor, false, false>();
        _llk_packer_wait_for_math_done_();
        _llk_pack_(0, (std::uint32_t)buffer_Dest/16-1);
    }

    void nop(){}

    /* Function for assigning elemtens of kernerls array to some of kernels */
    void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &pack_Dest_kernel;
        }else{
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[i] = &pack_Dest_kernel;
            } else {
                kernels[i] = &nop;
            }
        }
        va_end(args);
    }

#endif

#endif