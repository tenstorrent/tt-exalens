#ifndef MATH_KERNELS_HPP
#define MATH_KERNELS_HPP

#ifdef LLK_TRISC_MATH

    #include "llk_math_eltwise_binary.h"
    #include "params.h"
    void(*kernels[KERN_CNT])(void);

    void elwadd_kernel(){
        _llk_math_eltwise_binary_init_<EltwiseBinaryType::ELWADD, BroadcastType::NONE>(4, 0, 0);
        _llk_math_eltwise_binary_<EltwiseBinaryType::ELWADD, BroadcastType::NONE>(4, 0, true);
        set_math_semaphores();
    }

    void elwsub_kernel(){
        _llk_math_eltwise_binary_init_<EltwiseBinaryType::ELWSUB, BroadcastType::NONE>(4, 0, 0);
        _llk_math_eltwise_binary_<EltwiseBinaryType::ELWSUB, BroadcastType::NONE>(4, 0, true);
        set_math_semaphores();
    }

    void elwmul_kernel(){
        _llk_math_eltwise_binary_init_<EltwiseBinaryType::ELWMUL, BroadcastType::NONE>(4, 0, 0);
        _llk_math_eltwise_binary_<EltwiseBinaryType::ELWMUL, BroadcastType::NONE>(4, 0, true);
        set_math_semaphores();
    }

    //TODO: ADD MORE

    void nop(){}

    /* Function for assigning elemtens of kernerls array to some of kernels */
    void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &elwadd_kernel;
        } else if(first == 2){
            kernels[0] = &elwsub_kernel;
        }else if(first == 3){
            kernels[0] &elwmul_kernel
        }
        else {
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[0] = &elwadd_kernel;
            } else if(num == 2){
                kernels[0] = &elwsub_kernel;
            }else if(num == 3){
                kernels[0] &elwmul_kernel
            }
            else {
                kernels[0] = &nop;
            }
        }
        va_end(args);
    }

#endif

#endif