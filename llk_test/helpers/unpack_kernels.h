#ifndef UNPACK_KERNELS_HPP
#define UNPACK_KERNELS_HPP

#ifdef LLK_TRISC_UNPACK
    
    #include <cstdarg> 
    #include "llk_unpack_AB.h"
    #include "llk_unpack_common.h"
    #include "params.h"

    volatile uint32_t* buffer_A = (volatile uint32_t*)0x1b000;
    volatile uint32_t* buffer_B = (volatile uint32_t*)0x1c000;
    void(*kernels[KERN_CNT])(void);

    void unpack_A_kernel(){
        _llk_unpack_A_hw_configure_(DATA_FORMAT,DATA_FORMAT);
        _llk_unpack_A_init_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>(0, 0, FACE_R_DIM, 4, DATA_FORMAT, DATA_FORMAT);
        _llk_unpack_A_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>((((uint32_t)&buffer)/16)-1, 0, DATA_FORMAT, DATA_FORMAT);
    }

    void unpack_AB_kernel(){
        _llk_unpack_AB_hw_configure_(DATA_FORMAT, DATA_FORMAT, DATA_FORMAT, DATA_FORMAT);
        _llk_unpack_AB_init_<>();
        _llk_unpack_AB_<>((std::uint32_t)buffer_A/16-1,(std::uint32_t)buffer_B/16-1);
    }

    void nop(){}

        /* Function for assigning elemtens of kernerls array to some of kernels */
    void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &unpack_A_kernel;
        } else if(first == 2){
            kernels[0] = &unpack_AB_kernel;
        } else {
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[i] = &unpack_A_kernel;
            } else if(num == 2){
                kernels[i] = &unpack_AB_kernel;
            } else {
                kernels[i] = &nop;
            }
        }
        va_end(args);
    }

#endif

#endif