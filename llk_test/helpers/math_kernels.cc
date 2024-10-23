#include "math_kernels.h"
#include "params.h"
#include "llk_math_eltwise_binary.h"

    void(*kernels[10])(void);

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

    void nop(){}

    //TODO: ADD MORE