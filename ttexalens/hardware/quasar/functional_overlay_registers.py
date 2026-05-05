# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.register_store import RegisterDescription


class ClusterControlRegisterDescription(RegisterDescription):
    pass


class ControlStatusRegisterDescription(RegisterDescription):
    pass


class OverlayLlkTileCountersRegisterDescription(RegisterDescription):
    pass


class OverlayDebugRegisterDescription(RegisterDescription):
    pass


class RoccAcellRegisterDescription(RegisterDescription):
    pass


class SmnRegisterDescription(RegisterDescription):
    pass


class NeoRegisterDescription(RegisterDescription):
    pass


# Register map for Quasar overlay cluster control block.
# Each register group has its own base address (see _get_overlay_register_base_address
# in functional_overlay_block.py). Offsets are relative to each group's base address.
#
# Reset vector registers are 64-bit (8-byte stride); only lower 32 bits are accessed here.
# WB PC registers are 64-bit (8-byte stride); only lower 32 bits are accessed here.

register_map: dict[str, RegisterDescription] = {
    # ---------------------------------------------------------------------------
    # Reset vectors — 64-bit, 8-byte stride (cores 0-7)
    # Each register contains the address of the first instruction executed by corresponding core after reset.
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_RESET_VECTOR_0": ClusterControlRegisterDescription(offset=0x000),
    "TT_CLUSTER_CTRL_RESET_VECTOR_1": ClusterControlRegisterDescription(offset=0x008),
    "TT_CLUSTER_CTRL_RESET_VECTOR_2": ClusterControlRegisterDescription(offset=0x010),
    "TT_CLUSTER_CTRL_RESET_VECTOR_3": ClusterControlRegisterDescription(offset=0x018),
    "TT_CLUSTER_CTRL_RESET_VECTOR_4": ClusterControlRegisterDescription(offset=0x020),
    "TT_CLUSTER_CTRL_RESET_VECTOR_5": ClusterControlRegisterDescription(offset=0x028),
    "TT_CLUSTER_CTRL_RESET_VECTOR_6": ClusterControlRegisterDescription(offset=0x030),
    "TT_CLUSTER_CTRL_RESET_VECTOR_7": ClusterControlRegisterDescription(offset=0x038),
    # ---------------------------------------------------------------------------
    # Scratch registers — 32-bit, 4-byte stride
    # Per-core postcode/scratch layout:
    #   Core N postcode: SCRATCH_{2*N} at offset 0x040 + N*8
    #   Core N scratch:  SCRATCH_{2*N+1} at offset 0x044 + N*8
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_SCRATCH_0": ClusterControlRegisterDescription(offset=0x040),
    "TT_CLUSTER_CTRL_SCRATCH_1": ClusterControlRegisterDescription(offset=0x044),
    "TT_CLUSTER_CTRL_SCRATCH_2": ClusterControlRegisterDescription(offset=0x048),
    "TT_CLUSTER_CTRL_SCRATCH_3": ClusterControlRegisterDescription(offset=0x04C),
    "TT_CLUSTER_CTRL_SCRATCH_4": ClusterControlRegisterDescription(offset=0x050),
    "TT_CLUSTER_CTRL_SCRATCH_5": ClusterControlRegisterDescription(offset=0x054),
    "TT_CLUSTER_CTRL_SCRATCH_6": ClusterControlRegisterDescription(offset=0x058),
    "TT_CLUSTER_CTRL_SCRATCH_7": ClusterControlRegisterDescription(offset=0x05C),
    "TT_CLUSTER_CTRL_SCRATCH_8": ClusterControlRegisterDescription(offset=0x060),
    "TT_CLUSTER_CTRL_SCRATCH_9": ClusterControlRegisterDescription(offset=0x064),
    "TT_CLUSTER_CTRL_SCRATCH_10": ClusterControlRegisterDescription(offset=0x068),
    "TT_CLUSTER_CTRL_SCRATCH_11": ClusterControlRegisterDescription(offset=0x06C),
    "TT_CLUSTER_CTRL_SCRATCH_12": ClusterControlRegisterDescription(offset=0x070),
    "TT_CLUSTER_CTRL_SCRATCH_13": ClusterControlRegisterDescription(offset=0x074),
    "TT_CLUSTER_CTRL_SCRATCH_14": ClusterControlRegisterDescription(offset=0x078),
    "TT_CLUSTER_CTRL_SCRATCH_15": ClusterControlRegisterDescription(offset=0x07C),
    "TT_CLUSTER_CTRL_SCRATCH_16": ClusterControlRegisterDescription(offset=0x080),
    "TT_CLUSTER_CTRL_SCRATCH_17": ClusterControlRegisterDescription(offset=0x084),
    "TT_CLUSTER_CTRL_SCRATCH_18": ClusterControlRegisterDescription(offset=0x088),
    "TT_CLUSTER_CTRL_SCRATCH_19": ClusterControlRegisterDescription(offset=0x08C),
    "TT_CLUSTER_CTRL_SCRATCH_20": ClusterControlRegisterDescription(offset=0x090),
    "TT_CLUSTER_CTRL_SCRATCH_21": ClusterControlRegisterDescription(offset=0x094),
    "TT_CLUSTER_CTRL_SCRATCH_22": ClusterControlRegisterDescription(offset=0x098),
    "TT_CLUSTER_CTRL_SCRATCH_23": ClusterControlRegisterDescription(offset=0x09C),
    "TT_CLUSTER_CTRL_SCRATCH_24": ClusterControlRegisterDescription(offset=0x0A0),
    "TT_CLUSTER_CTRL_SCRATCH_25": ClusterControlRegisterDescription(offset=0x0A4),
    "TT_CLUSTER_CTRL_SCRATCH_26": ClusterControlRegisterDescription(offset=0x0A8),
    "TT_CLUSTER_CTRL_SCRATCH_27": ClusterControlRegisterDescription(offset=0x0AC),
    "TT_CLUSTER_CTRL_SCRATCH_28": ClusterControlRegisterDescription(offset=0x0B0),
    "TT_CLUSTER_CTRL_SCRATCH_29": ClusterControlRegisterDescription(offset=0x0B4),
    "TT_CLUSTER_CTRL_SCRATCH_30": ClusterControlRegisterDescription(offset=0x0B8),
    "TT_CLUSTER_CTRL_SCRATCH_31": ClusterControlRegisterDescription(offset=0x0BC),
    # ---------------------------------------------------------------------------
    # ROCC memory chicken bits — affects performance, not functionality.
    # Default value: 0x0000002E
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_ROCC_MEM_CHICKEN": ClusterControlRegisterDescription(offset=0x0C0),
    # ---------------------------------------------------------------------------
    # Scatter list magic number — 64-bit value split across LO/HI registers.
    # Used to identify/validate scatter list entries; values above this threshold
    # are treated as end-of-list markers or special entries.
    # Default value: 0xFFFFFFFF_FFFFFFFF
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_SCATTER_LIST_MAGIC_NUM_LO": ClusterControlRegisterDescription(offset=0x0C4),
    "TT_CLUSTER_CTRL_SCATTER_LIST_MAGIC_NUM_HI": ClusterControlRegisterDescription(offset=0x0C8),
    # ---------------------------------------------------------------------------
    # Clock gating control — each bit enables clock gating for a functional block
    # (power saving: clock disabled when block is idle). Default 0x0 = all clocks
    # always running. Disable clock gating (write 0) for debug to keep all clocks active.
    # Bits: [0]=rocc, [1]=idma, [2]=cluster_ctrl, [3]=context_switch, [4]=llk_intf,
    #       [5]=snoop, [6]=rsvd, [7]=l1_flex_client_idma, [8]=l1_flex_client_overlay
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_CLOCK_GATING": ClusterControlRegisterDescription(offset=0x0CC),
    # Clock gating hysteresis — 7-bit value; sets the idle delay before the clock
    # gate closes, preventing rapid toggling during short bursts of activity.
    # Default value: 0x08
    "TT_CLUSTER_CTRL_CLOCK_GATING_HYST": ClusterControlRegisterDescription(offset=0x0D0),
    # ---------------------------------------------------------------------------
    # WB (write-back) PC registers — 64-bit, 8-byte stride (cores 0-7).
    # Lower 32 bits hold the instruction address for programs < 4 GB.
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_WB_PC_REG_C0": ClusterControlRegisterDescription(offset=0x0D8),
    "TT_CLUSTER_CTRL_WB_PC_REG_C1": ClusterControlRegisterDescription(offset=0x0E0),
    "TT_CLUSTER_CTRL_WB_PC_REG_C2": ClusterControlRegisterDescription(offset=0x0E8),
    "TT_CLUSTER_CTRL_WB_PC_REG_C3": ClusterControlRegisterDescription(offset=0x0F0),
    "TT_CLUSTER_CTRL_WB_PC_REG_C4": ClusterControlRegisterDescription(offset=0x0F8),
    "TT_CLUSTER_CTRL_WB_PC_REG_C5": ClusterControlRegisterDescription(offset=0x100),
    "TT_CLUSTER_CTRL_WB_PC_REG_C6": ClusterControlRegisterDescription(offset=0x108),
    "TT_CLUSTER_CTRL_WB_PC_REG_C7": ClusterControlRegisterDescription(offset=0x110),
    # Capture enable/disable (enable by default)
    "TT_CLUSTER_CTRL_WB_PC_CTRL": ClusterControlRegisterDescription(offset=0x118),
    # ---------------------------------------------------------------------------
    # Misc cluster ctrl registers
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_ECC_PARITY_CONTROL": ClusterControlRegisterDescription(offset=0x11C),
    "TT_CLUSTER_CTRL_ECC_PARITY_STATUS": ClusterControlRegisterDescription(offset=0x120),
    # NoC snoop TileLink master configuration — controls cache coherency behaviour
    # between overlay core and L2 cache.
    # Bits: [0]=disable_inline_writes (0=inline writes enabled),
    #       [1]=invalidate_flush_dirty_en (1=flush dirty lines on invalidate),
    #       [2]=clean_putdata_en (1=send clean PutData to L2)
    # Default value: 0x00000006
    "TT_CLUSTER_CTRL_NOC_SNOOP_TL_MASTER_CFG": ClusterControlRegisterDescription(offset=0x124),
    "TT_CLUSTER_CTRL_ASSERTS": ClusterControlRegisterDescription(offset=0x128),
    # ---------------------------------------------------------------------------
    # Prefetcher control — enables/configures icache and dcache prefetchers.
    # Bits: [7:0]=dcache_prefetcher_ctrl, [8]=dcache_prefetcher_waitforhit,
    #       [14:9]=dcache_prefetcher_ahead, [22:15]=icache_prefetcher_ctrl,
    #       [23]=icache_prefetcher_waitforhit, [29:24]=icache_prefetcher_ahead
    # Default value: 0x027F84FF
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_PREFETCHER_CONTROL": ClusterControlRegisterDescription(offset=0x12C),
    # ---------------------------------------------------------------------------
    # Bus Error Unit (BEU) data — per-core read-only error status registers.
    # 64-bit, 8-byte stride (one per Rocket core). Captures icache/dcache
    # TileLink bus errors, ECC/parity errors, faulting address, and BEU cause.
    # Bits: [0]=icache_tl_bus_error, [1]=dcache_tl_bus_error,
    #       [2]=icache_parity_uncorrectable, [3]=dcache_ecc_correctable,
    #       [4]=dcache_ecc_uncorrectable, [56:5]=dcache_error_addr,
    #       [59:57]=beu_cause_reg
    # Default value: 0x0000000000000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C0": ClusterControlRegisterDescription(offset=0x130),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C1": ClusterControlRegisterDescription(offset=0x138),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C2": ClusterControlRegisterDescription(offset=0x140),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C3": ClusterControlRegisterDescription(offset=0x148),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C4": ClusterControlRegisterDescription(offset=0x150),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C5": ClusterControlRegisterDescription(offset=0x158),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C6": ClusterControlRegisterDescription(offset=0x160),
    "TT_CLUSTER_CTRL_BUS_ERROR_UNIT_DATA_C7": ClusterControlRegisterDescription(offset=0x168),
    # ---------------------------------------------------------------------------
    # L2 directory error status — 4 registers, one per directory slice.
    # Part of the RAS infrastructure. Bits: [1:0]=error, [7:2]=error_index.
    # Default value: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_L2_DIR_ERRORS_0": ClusterControlRegisterDescription(offset=0x170),
    "TT_CLUSTER_CTRL_L2_DIR_ERRORS_1": ClusterControlRegisterDescription(offset=0x174),
    "TT_CLUSTER_CTRL_L2_DIR_ERRORS_2": ClusterControlRegisterDescription(offset=0x178),
    "TT_CLUSTER_CTRL_L2_DIR_ERRORS_3": ClusterControlRegisterDescription(offset=0x17C),
    # ---------------------------------------------------------------------------
    # L2 bank error status — 16 registers, one per L2 cache bank.
    # Part of the RAS infrastructure. Bits: [1:0]=error, [9:2]=error_index.
    # Default value: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_0": ClusterControlRegisterDescription(offset=0x180),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_1": ClusterControlRegisterDescription(offset=0x184),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_2": ClusterControlRegisterDescription(offset=0x188),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_3": ClusterControlRegisterDescription(offset=0x18C),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_4": ClusterControlRegisterDescription(offset=0x190),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_5": ClusterControlRegisterDescription(offset=0x194),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_6": ClusterControlRegisterDescription(offset=0x198),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_7": ClusterControlRegisterDescription(offset=0x19C),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_8": ClusterControlRegisterDescription(offset=0x1A0),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_9": ClusterControlRegisterDescription(offset=0x1A4),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_10": ClusterControlRegisterDescription(offset=0x1A8),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_11": ClusterControlRegisterDescription(offset=0x1AC),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_12": ClusterControlRegisterDescription(offset=0x1B0),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_13": ClusterControlRegisterDescription(offset=0x1B4),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_14": ClusterControlRegisterDescription(offset=0x1B8),
    "TT_CLUSTER_CTRL_L2_BANKS_ERRORS_15": ClusterControlRegisterDescription(offset=0x1BC),
    "TT_CLUSTER_CTRL_DEBUG_DMACTIVE": ClusterControlRegisterDescription(offset=0x1C0),
    "TT_CLUSTER_CTRL_DEBUG_DMACTIVEACK": ClusterControlRegisterDescription(offset=0x1C4),
    # ---------------------------------------------------------------------------
    # T6 L1 CSR block — base address: 0x03000200
    # Configures and monitors the L1 memory flex client ports: address hashing
    # for bank interleaving, in-order transaction enforcement, and per-port
    # read/write control and status.
    # ---------------------------------------------------------------------------
    # Group hash function control — enables/disables the two address hash
    # functions (fn0, fn1) used to distribute L1 accesses across banks.
    # Bits: [0]=hash_fn0_en, [1]=hash_fn1_en. Default: 0x00000000
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN_CTRL": ControlStatusRegisterDescription(offset=0x000),
    # ---------------------------------------------------------------------------
    # Hash function 0 — selects and permutes address bits for bank interleaving.
    # MASK/MATCH select which addresses the function applies to (bits [21:10]).
    # ADDR4–ADDR11 map input address bits to hash inputs (bits [21:4]).
    # SWAP_ADDR10–21 permute address bits within the hash (bits [2:0] each).
    # MASK default: 0x00000000, MATCH default: 0x003FFC00,
    # ADDR* default: 0x00000800, SWAP_ADDR* default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_MASK": ControlStatusRegisterDescription(offset=0x004),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_MATCH": ControlStatusRegisterDescription(offset=0x008),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR4": ControlStatusRegisterDescription(offset=0x00C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR5": ControlStatusRegisterDescription(offset=0x010),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR6": ControlStatusRegisterDescription(offset=0x014),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR7": ControlStatusRegisterDescription(offset=0x018),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR8": ControlStatusRegisterDescription(offset=0x01C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR9": ControlStatusRegisterDescription(offset=0x020),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR10": ControlStatusRegisterDescription(offset=0x024),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_ADDR11": ControlStatusRegisterDescription(offset=0x028),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR10": ControlStatusRegisterDescription(offset=0x02C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR11": ControlStatusRegisterDescription(offset=0x030),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR12": ControlStatusRegisterDescription(offset=0x034),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR13": ControlStatusRegisterDescription(offset=0x038),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR14": ControlStatusRegisterDescription(offset=0x03C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR15": ControlStatusRegisterDescription(offset=0x040),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR16": ControlStatusRegisterDescription(offset=0x044),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR17": ControlStatusRegisterDescription(offset=0x048),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR18": ControlStatusRegisterDescription(offset=0x04C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR19": ControlStatusRegisterDescription(offset=0x050),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR20": ControlStatusRegisterDescription(offset=0x054),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN0_SWAP_ADDR21": ControlStatusRegisterDescription(offset=0x058),
    # ---------------------------------------------------------------------------
    # Hash function 1 — identical structure to fn0, second independent hash
    # function for L1 bank interleaving.
    # MASK default: 0x00000000, MATCH default: 0x003FFC00,
    # ADDR* default: 0x00000800, SWAP_ADDR* default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_MASK": ControlStatusRegisterDescription(offset=0x05C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_MATCH": ControlStatusRegisterDescription(offset=0x060),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR4": ControlStatusRegisterDescription(offset=0x064),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR5": ControlStatusRegisterDescription(offset=0x068),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR6": ControlStatusRegisterDescription(offset=0x06C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR7": ControlStatusRegisterDescription(offset=0x070),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR8": ControlStatusRegisterDescription(offset=0x074),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR9": ControlStatusRegisterDescription(offset=0x078),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR10": ControlStatusRegisterDescription(offset=0x07C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_ADDR11": ControlStatusRegisterDescription(offset=0x080),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR10": ControlStatusRegisterDescription(offset=0x084),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR11": ControlStatusRegisterDescription(offset=0x088),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR12": ControlStatusRegisterDescription(offset=0x08C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR13": ControlStatusRegisterDescription(offset=0x090),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR14": ControlStatusRegisterDescription(offset=0x094),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR15": ControlStatusRegisterDescription(offset=0x098),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR16": ControlStatusRegisterDescription(offset=0x09C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR17": ControlStatusRegisterDescription(offset=0x0A0),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR18": ControlStatusRegisterDescription(offset=0x0A4),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR19": ControlStatusRegisterDescription(offset=0x0A8),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR20": ControlStatusRegisterDescription(offset=0x0AC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_GROUP_HASH_FN1_SWAP_ADDR21": ControlStatusRegisterDescription(offset=0x0B0),
    # ---------------------------------------------------------------------------
    # In-order transaction enforcement — forces L1 accesses matching the address
    # pattern (MASK & addr == MATCH) to be issued in order, ensuring memory
    # consistency for specific address ranges.
    # Bits [21:4]: bit_sel. IN_ORDER_MASK default: 0x00000000,
    # IN_ORDER_MATCH default: 0x003FFFF0
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_IN_ORDER_MASK": ControlStatusRegisterDescription(offset=0x0B4),
    "TT_CLUSTER_CTRL_T6_L1_CSR_IN_ORDER_MATCH": ControlStatusRegisterDescription(offset=0x0B8),
    # ---------------------------------------------------------------------------
    # RW (read-write) port control — 6 ports. Per-port ordering enforcement for
    # combined read/write flex client ports.
    # Bits: [0]=all_in_order, [1]=write_in_order, [2]=rw_barrier_order
    # Default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_0": ControlStatusRegisterDescription(offset=0x0BC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_1": ControlStatusRegisterDescription(offset=0x0C0),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_2": ControlStatusRegisterDescription(offset=0x0C4),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_3": ControlStatusRegisterDescription(offset=0x0C8),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_4": ControlStatusRegisterDescription(offset=0x0CC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_CTRL_5": ControlStatusRegisterDescription(offset=0x0D0),
    # RW port status for NoC atomic operations — same error bitfields as
    # WR_PORT_STATUS but tracks atomic op errors over the NoC.
    # Bits: [0]=fp_error, [1]=fp_nan, [2]=fp_overflow, [3]=fp_underflow,
    #       [4]=int_overflow, [5]=fifo_parity_err. Default: 0x00000000
    "TT_CLUSTER_CTRL_T6_L1_CSR_RW_PORT_STATUS_NOC_ATOMIC": ControlStatusRegisterDescription(offset=0x0D4),
    # ---------------------------------------------------------------------------
    # RD (read-only) port control — 8 ports. Per-port ordering enforcement for
    # read-only flex client ports.
    # Bits: [0]=all_in_order, [1]=write_in_order, [2]=rw_barrier_order
    # Default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_0": ControlStatusRegisterDescription(offset=0x0D8),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_1": ControlStatusRegisterDescription(offset=0x0DC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_2": ControlStatusRegisterDescription(offset=0x0E0),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_3": ControlStatusRegisterDescription(offset=0x0E4),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_4": ControlStatusRegisterDescription(offset=0x0E8),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_5": ControlStatusRegisterDescription(offset=0x0EC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_6": ControlStatusRegisterDescription(offset=0x0F0),
    "TT_CLUSTER_CTRL_T6_L1_CSR_RD_PORT_CTRL_7": ControlStatusRegisterDescription(offset=0x0F4),
    # ---------------------------------------------------------------------------
    # WR (write-only) port control — 8 ports. Per-port ordering enforcement for
    # write-only flex client ports.
    # Bits: [0]=all_in_order, [1]=write_in_order, [2]=rw_barrier_order
    # Default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_0": ControlStatusRegisterDescription(offset=0x0F8),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_1": ControlStatusRegisterDescription(offset=0x0FC),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_2": ControlStatusRegisterDescription(offset=0x100),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_3": ControlStatusRegisterDescription(offset=0x104),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_4": ControlStatusRegisterDescription(offset=0x108),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_5": ControlStatusRegisterDescription(offset=0x10C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_6": ControlStatusRegisterDescription(offset=0x110),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_CTRL_7": ControlStatusRegisterDescription(offset=0x114),
    # ---------------------------------------------------------------------------
    # WR port status — 8 ports. Read-only error flags per write port.
    # Bits: [0]=fp_error, [1]=fp_nan, [2]=fp_overflow, [3]=fp_underflow,
    #       [4]=int_overflow, [5]=fifo_parity_err. Default: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_0": ControlStatusRegisterDescription(offset=0x118),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_1": ControlStatusRegisterDescription(offset=0x11C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_2": ControlStatusRegisterDescription(offset=0x120),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_3": ControlStatusRegisterDescription(offset=0x124),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_4": ControlStatusRegisterDescription(offset=0x128),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_5": ControlStatusRegisterDescription(offset=0x12C),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_6": ControlStatusRegisterDescription(offset=0x130),
    "TT_CLUSTER_CTRL_T6_L1_CSR_WR_PORT_STATUS_7": ControlStatusRegisterDescription(offset=0x134),
    # ---------------------------------------------------------------------------
    # Snoop debug status — read-only TileLink request FIFO state.
    # Bits: [0]=debug_tl_req_fifo_empty, [1]=debug_tl_req_fifo_full,
    #       [2]=debug_tl_req_in_progress
    # Default value: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_DEBUG_SNOOP": ClusterControlRegisterDescription(offset=0x338),
    # Overlay hardware info — read-only. Reports overlay/NoC/Tensix versions and
    # presence of hardware features (PLL, SmnRegisterDescription, dispatch instruction, etc.).
    # Bits: [0]=dispatch_inst, [1]=is_customer, [2]=has_pll, [3]=has_smn,
    #       [9:4]=tensix_version, [15:10]=noc_version, [21:16]=overlay_version
    # Default value: 0x00000000
    "TT_CLUSTER_CTRL_OVERLAY_INFO": ClusterControlRegisterDescription(offset=0x33C),
    # Software RAS signaling — single-bit register for software-driven
    # Reliability/Availability/Serviceability error injection or reporting.
    # Default value: 0x00000000
    "TT_CLUSTER_CTRL_SW_RAS": ClusterControlRegisterDescription(offset=0x340),
    # SBUS RSINK fallback reset control — controls fallback reset behaviour
    # for the SBUS sink logic. Default value: 0x00000000
    "TT_CLUSTER_CTRL_SBUS_RSINK_RESET_FALLBACK": ClusterControlRegisterDescription(offset=0x344),
    # ---------------------------------------------------------------------------
    # Overlay chicken bits — feature enable/disable for overlay and L1 region.
    # Bits: [0]=l1_region_en (enables L1 accessible region checking),
    #       [1]=snoop_perf_disable (disables snoop performance features)
    # Default value: 0x00000000
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CTRL_OVERLAY_CHICKEN_BITS": ClusterControlRegisterDescription(offset=0x348),
    # L1 accessible region bounds — defines the valid address window for L1 access.
    # Bits: [15:0]=start_addr, [31:16]=end_addr
    # Default value: 0xFFFF0000 (full range enabled by default)
    "TT_CLUSTER_CTRL_L1_ACCESSIBLE_REGION": ClusterControlRegisterDescription(offset=0x34C),
    # L1 region access error — set when an access falls outside the L1 accessible
    # region defined by L1_ACCESSIBLE_REGION (requires l1_region_en=1 in OVERLAY_CHICKEN_BITS).
    # Bits: [0]=error, [16:1]=error_addr
    # Default value: 0x00000000
    "TT_CLUSTER_CTRL_L1_REGION_ERROR": ClusterControlRegisterDescription(offset=0x350),
    # ---------------------------------------------------------------------------
    # OverlayLlkTileCountersRegisterDescription — base address: 0x03003000
    #
    # Hardware tile counter registers for producer/consumer synchronization in
    # the dataflow pipeline between compute and data movement engines.
    # Two LLK interfaces are provided (TT_LLK_INTERFACE at 0x03003000 and
    # TT_LLK_INTERFACE_1 at 0x03003400), each with 16 tile counter groups
    # (groups 0–15, spaced 0x40 bytes apart).
    #
    # Per-group registers (offsets relative to group base):
    #   RESET            (+0x04): Write 1 to reset all counters in this group.
    #   POSTED           (+0x08): Producer increments tiles posted (write-only).
    #   ACKED            (+0x0C): Consumer increments tiles acknowledged (write-only).
    #   BUFFER_CAPACITY  (+0x10): Software programs max tile capacity of buffer.
    #   READ_POSTED      (+0x14): Read current posted counter value.
    #   READ_ACKED       (+0x18): Read current acked counter value.
    #   ERROR_STATUS     (+0x1C): Error flags (overflow/underflow conditions).
    #   TILES_AVAIL_THRESHOLD (+0x38): Threshold for tiles-available interrupt/status.
    #   TILES_FREE_THRESHOLD  (+0x3C): Threshold for tiles-free interrupt/status.
    #
    # All counters default to 0 after reset; BUFFER_CAPACITY must be programmed.
    # ---------------------------------------------------------------------------
    # TT_LLK_INTERFACE — 16 tile counter groups, base: 0x03003000
    # ---------------------------------------------------------------------------
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x004
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x008
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x00C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x010
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x014
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x018
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x01C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x038
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_0__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x03C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x044
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x048
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x04C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x050
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x054
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x058
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x05C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x078
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_1__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x07C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x084
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x088
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x08C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x090
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x094
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x098
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x09C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x0B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_2__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x0BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x0C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x0C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x0CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x0D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x0D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x0D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x0DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x0F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_3__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x0FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x104
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x108
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x10C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x110
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x114
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x118
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x11C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x138
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_4__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x13C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x144
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x148
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x14C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x150
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x154
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x158
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x15C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x178
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_5__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x17C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x184
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x188
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x18C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x190
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x194
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x198
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x19C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x1B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_6__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x1BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x1C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x1C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x1CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x1D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x1D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x1D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x1DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x1F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_7__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x1FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x204
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x208
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x20C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x210
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x214
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x218
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x21C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x238
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_8__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x23C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x244
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x248
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x24C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x250
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x254
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x258
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x25C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x278
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_9__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x27C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x284
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x288
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x28C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x290
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x294
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x298
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x29C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x2B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_10__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x2BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x2C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x2C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x2CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x2D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x2D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x2D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x2DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x2F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_11__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x2FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x304
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x308
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x30C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x310
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x314
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x318
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x31C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x338
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_12__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x33C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x344
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x348
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x34C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x350
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x354
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x358
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x35C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x378
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_13__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x37C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x384
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x388
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x38C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x390
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x394
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x398
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x39C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x3B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_14__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x3BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x3C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x3C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x3CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x3D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x3D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x3D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x3DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x3F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_15__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x3FC
    ),
    # ---------------------------------------------------------------------------
    # TT_LLK_INTERFACE_1 — 16 tile counter groups, base: 0x03003400
    # Identical structure to TT_LLK_INTERFACE; second independent LLK interface.
    # ---------------------------------------------------------------------------
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x404
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x408
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x40C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x410
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x414
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x418
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x41C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x438
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_0__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x43C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x444
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x448
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x44C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x450
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x454
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x458
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x45C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x478
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_1__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x47C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x484
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x488
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x48C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x490
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x494
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x498
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x49C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x4B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_2__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x4BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x4C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x4C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x4CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x4D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x4D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x4D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x4DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x4F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_3__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x4FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x504
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x508
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x50C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x510
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x514
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x518
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x51C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x538
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_4__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x53C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x544
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x548
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x54C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x550
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x554
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x558
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x55C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x578
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_5__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x57C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x584
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x588
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x58C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x590
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x594
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x598
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x59C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x5B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_6__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x5BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x5C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x5C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x5CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x5D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x5D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x5D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x5DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x5F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_7__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x5FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x604
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x608
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x60C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x610
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x614
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x618
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x61C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x638
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_8__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x63C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x644
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x648
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x64C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x650
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x654
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x658
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x65C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x678
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_9__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x67C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x684
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x688
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x68C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x690
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x694
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x698
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x69C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x6B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_10__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x6BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x6C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x6C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x6CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x6D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x6D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x6D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x6DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x6F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_11__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x6FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x704
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x708
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x70C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x710
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x714
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x718
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x71C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x738
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_12__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x73C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x744
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x748
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x74C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x750
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x754
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x758
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x75C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x778
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_13__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x77C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x784
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x788
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x78C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x790
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x794
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x798
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x79C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x7B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_14__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x7BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x7C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x7C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x7CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x7D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x7D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x7D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x7DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x7F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_15__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x7FC
    ),
    # ---------------------------------------------------------------------------
    # Debug Module APB registers (TT_DEBUG_MODULE_APB at 0x0300A000).
    # Offsets are relative to the OverlayDebugRegisterDescription base address 0x0300A000,
    # so each APB register offset = DMI_addr * 4.
    # ---------------------------------------------------------------------------
    "TT_DEBUG_MODULE_APB_DATA0": OverlayDebugRegisterDescription(offset=0x010),
    "TT_DEBUG_MODULE_APB_DATA1": OverlayDebugRegisterDescription(offset=0x014),
    "TT_DEBUG_MODULE_APB_DMCONTROL": OverlayDebugRegisterDescription(offset=0x040),
    "TT_DEBUG_MODULE_APB_DMSTATUS": OverlayDebugRegisterDescription(offset=0x044),
    "TT_DEBUG_MODULE_APB_HARTINFO": OverlayDebugRegisterDescription(offset=0x048),
    "TT_DEBUG_MODULE_APB_HALTSUMMARY1": OverlayDebugRegisterDescription(offset=0x04C),
    "TT_DEBUG_MODULE_APB_HAWINDOW": OverlayDebugRegisterDescription(offset=0x054),
    "TT_DEBUG_MODULE_APB_ABSTRACTCS": OverlayDebugRegisterDescription(offset=0x058),
    "TT_DEBUG_MODULE_APB_COMMAND": OverlayDebugRegisterDescription(offset=0x05C),
    "TT_DEBUG_MODULE_APB_ABSTRACTAUTO": OverlayDebugRegisterDescription(offset=0x060),
    "TT_DEBUG_MODULE_APB_PROGBUF0": OverlayDebugRegisterDescription(offset=0x080),
    "TT_DEBUG_MODULE_APB_SBCS": OverlayDebugRegisterDescription(offset=0x0E0),
    "TT_DEBUG_MODULE_APB_SBADDR0": OverlayDebugRegisterDescription(offset=0x0E4),
    "TT_DEBUG_MODULE_APB_SBADDR1": OverlayDebugRegisterDescription(offset=0x0E8),
    "TT_DEBUG_MODULE_APB_SBDATA0": OverlayDebugRegisterDescription(offset=0x0F0),
    "TT_DEBUG_MODULE_APB_SBDATA1": OverlayDebugRegisterDescription(offset=0x0F4),
    "TT_DEBUG_MODULE_APB_HALTSUMMARY0": OverlayDebugRegisterDescription(offset=0x100),
    # ---------------------------------------------------------------------------
    # SmnRegisterDescription registers
    # ---------------------------------------------------------------------------
    "SMN_RISC_RESET_REG": SmnRegisterDescription(offset=0x79B0),
}
