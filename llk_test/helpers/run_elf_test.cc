// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include "ckernel.h"
#include "ckernel_addr_map.h"
#include "ckernel_pcbuf.h"
#include "ckernel_main.h"
#include "ckernel_globals.h"
#include <l1_address_map.h>
#include <tensix.h>

// Necessary for every test. Don't change
// **********************************************************************

namespace ckernel{
	volatile uint tt_reg_ptr *pc_buf_base = reinterpret_cast<volatile uint *>(PC_BUF_BASE);
	volatile uint tt_reg_ptr *instrn_buffer = reinterpret_cast<volatile uint *>(INSTRN_BUF_BASE);
	volatile uint tt_reg_ptr *regfile = reinterpret_cast<volatile uint *>(REGFILE_BASE);
	volatile uint tt_l1_ptr * trisc_l1_mailbox = reinterpret_cast<volatile uint tt_l1_ptr *>(0x1d000);

	volatile uint32_t inst_trace_ptr  __attribute__((section(".init"))) = 0;
	volatile uint32_t inst_trace[1024]  __attribute__((section(".init"))) = {0};

	uint32_t cfg_state_id __attribute__((section(".bss"))) = 0;  // Flip between 0 and 1 to keep state between kernel calls
	uint32_t dest_offset_id __attribute__((section(".bss"))) = 0; // Flip between 0 and 1 to keep dest pointer between kernel calls
}

using namespace ckernel;

// **********************************************************************

/*  Not using existing mailbox because it's content can get overriden by some other code.
	Pointers to some addresses outside of code sections of TRISC cores are set to be used as mailboxes.
	Usage is still the same. If kernel completed successfully data in mailbox will be 1.
*/

#ifdef LLK_TRISC_PACK
volatile uint32_t* mailbox = (volatile uint32_t*)(0x19FFC);
#endif
#ifdef LLK_TRISC_MATH
volatile uint32_t* mailbox = (volatile uint32_t*)(0x19FF8);
#endif
#ifdef LLK_TRISC_UNPACK
volatile uint32_t* mailbox = (volatile uint32_t*)(0x19FF4);
#endif

int main()
{
    FWEVENT("Launching proudction env kernels");

	tensix_sync();
    run_kernel();

	*mailbox = KERNEL_COMPLETE; // 0x1

	for(;;){}
}