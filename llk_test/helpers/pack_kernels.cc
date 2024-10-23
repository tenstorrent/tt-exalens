#include "pack_kernels.h"
#include "llk_pack.h"
#include "llk_pack_common.h"
#include "params.h"

    volatile uint32_t* buffer_Dest = (volatile uint32_t*)0x1a000;
    void(*kernels[10])(void);

    void pack_Dest_kernel(){

        _llk_pack_hw_configure_(DATA_FORMAT, DATA_FORMAT, 16*16*4);
        _llk_pack_init_<false, false, DstTileFaceLayout::RowMajor, false>(DATA_FORMAT);
        _llk_pack_dest_init_<DstSync::SyncFull, DstTileFaceLayout::RowMajor, false, false>();
        _llk_packer_wait_for_math_done_();
        _llk_pack_(0, (std::uint32_t)buffer_Dest/16-1);
    }

    void nop(){}