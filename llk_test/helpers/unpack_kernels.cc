
#include "unpack_kernels.h"
#include "params.h"
#include "llk_unpack_A.h"
#include "llk_unpack_AB.h"
#include "llk_unpack_common.h"

    volatile uint32_t* buffer_A = (volatile uint32_t*)0x1b000;
    volatile uint32_t* buffer_B = (volatile uint32_t*)0x1c000;
    void(*kernels[10])(void);

    void unpack_A_kernel(){
        _llk_unpack_A_hw_configure_(DATA_FORMAT,DATA_FORMAT);
        _llk_unpack_A_init_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>(0, 0, FACE_R_DIM, 4, DATA_FORMAT, DATA_FORMAT);
        _llk_unpack_A_<BroadcastType::NONE, false, EltwiseBinaryReuseDestType::NONE, true>((((uint32_t)&buffer_A)/16)-1, 0, DATA_FORMAT, DATA_FORMAT);
    }

    void unpack_AB_kernel(){
        _llk_unpack_AB_hw_configure_(DATA_FORMAT, DATA_FORMAT, DATA_FORMAT, DATA_FORMAT);
        _llk_unpack_AB_init_<>();
        _llk_unpack_AB_<>((std::uint32_t)buffer_A/16-1,(std::uint32_t)buffer_B/16-1);
    }

    void nop(){}

