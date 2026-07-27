# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.register_store import DebugRegisterDescription, RegisterDescription


class ClusterControlRegisterDescription(RegisterDescription):
    pass


class ControlStatusRegisterDescription(RegisterDescription):
    pass


class OverlayLlkTileCountersRegisterDescription(RegisterDescription):
    pass


class RoccAcellRegisterDescription(RegisterDescription):
    pass


class SmnRegisterDescription(RegisterDescription):
    pass


class NeoRegisterDescription(RegisterDescription):
    pass


class BusErrorUnitRegisterDescription(RegisterDescription):
    pass


class WatchdogTimerRegisterDescription(RegisterDescription):
    pass


class ClintRegisterDescription(RegisterDescription):
    pass


class PlicRegisterDescription(RegisterDescription):
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
    # Four LLK interfaces are provided (TT_LLK_INTERFACE at 0x03003000,
    # TT_LLK_INTERFACE_1 at 0x03003400, TT_LLK_INTERFACE_2 at 0x03003800 and
    # TT_LLK_INTERFACE_3 at 0x03003C00), each with 16 tile counter groups
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
    # TT_LLK_INTERFACE_2 — 16 tile counter groups, base: 0x03003800
    # Identical structure to TT_LLK_INTERFACE; LLK interface 2.
    # ---------------------------------------------------------------------------
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x804
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x808
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x80C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x810
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x814
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x818
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x81C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x838
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_0__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x83C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x844
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x848
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x84C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x850
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x854
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x858
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x85C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x878
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_1__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x87C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x884
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x888
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x88C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x890
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x894
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x898
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x89C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x8B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_2__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x8BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x8C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x8C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x8CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x8D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x8D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x8D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x8DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x8F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_3__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x8FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x904
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x908
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x90C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x910
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x914
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x918
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x91C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x938
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_4__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x93C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x944
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x948
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x94C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x950
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x954
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x958
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x95C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x978
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_5__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x97C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x984
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x988
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x98C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x990
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x994
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x998
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x99C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x9B8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_6__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x9BC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0x9C4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x9C8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x9CC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0x9D0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0x9D4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0x9D8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0x9DC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x9F8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_7__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0x9FC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xA04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xA10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xA1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xA38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_8__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xA3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xA44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xA50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xA5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xA78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_9__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xA7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xA84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xA90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xA98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xA9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xAB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_10__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xABC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xAC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xAC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xACC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xAD0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xAD4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xAD8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xADC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xAF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_11__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xAFC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xB04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xB10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xB1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xB38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_12__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xB3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xB44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xB50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xB5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xB78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_13__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xB7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xB84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xB90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xB98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xB9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xBB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_14__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xBBC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xBC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xBC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xBCC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xBD0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xBD4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xBD8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xBDC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xBF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_15__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xBFC
    ),
    # ---------------------------------------------------------------------------
    # TT_LLK_INTERFACE_3 — 16 tile counter groups, base: 0x03003C00
    # Identical structure to TT_LLK_INTERFACE; LLK interface 3.
    # ---------------------------------------------------------------------------
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xC04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xC10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xC1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xC38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_0__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xC3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xC44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xC50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xC5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xC78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_1__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xC7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xC84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xC90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xC98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xC9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xCB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_2__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xCBC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xCC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xCC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xCCC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xCD0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xCD4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xCD8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xCDC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xCF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_3__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xCFC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xD04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xD10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xD1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xD38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_4__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xD3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xD44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xD50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xD5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xD78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_5__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xD7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xD84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xD90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xD98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xD9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xDB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_6__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xDBC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xDC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xDC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xDCC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xDD0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xDD4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xDD8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xDDC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xDF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_7__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xDFC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xE04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xE10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xE1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xE38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_8__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xE3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xE44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xE50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xE5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xE78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_9__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xE7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xE84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xE90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xE98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xE9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xEB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_10__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xEBC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xEC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xEC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xECC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xED0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xED4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xED8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xEDC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xEF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_11__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xEFC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xF04
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF08
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF0C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xF10
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF14
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF18
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xF1C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xF38
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_12__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xF3C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xF44
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF48
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF4C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xF50
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF54
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF58
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xF5C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xF78
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_13__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xF7C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xF84
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF88
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF8C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xF90
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF94
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xF98
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xF9C
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xFB8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_14__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xFBC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__RESET": OverlayLlkTileCountersRegisterDescription(
        offset=0xFC4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xFC8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xFCC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__BUFFER_CAPACITY": OverlayLlkTileCountersRegisterDescription(
        offset=0xFD0
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__READ_POSTED": OverlayLlkTileCountersRegisterDescription(
        offset=0xFD4
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__READ_ACKED": OverlayLlkTileCountersRegisterDescription(
        offset=0xFD8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__ERROR_STATUS": OverlayLlkTileCountersRegisterDescription(
        offset=0xFDC
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__TILES_AVAIL_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xFF8
    ),
    "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_15__TILES_FREE_THRESHOLD": OverlayLlkTileCountersRegisterDescription(
        offset=0xFFC
    ),
    # ---------------------------------------------------------------------------
    # RoccAcellRegisterDescription — base address: 0x03004000
    #
    # ROCC command-buffer register files: the descriptor of the in-flight NOC
    # transfer per Overlay CPU plus its interrupt/ack state. One cmd_buf_r
    # (read command buffer) register file per CPU (cpu0-cpu7), CPU stride 0xC00.
    # cpu0 base 0x03004000 ... cpu7 base 0x03009400.
    #
    # Fastest triage: IP + PER_TR_ID_IP_0/1/2 (stuck transfer / which tr_id),
    # WR_SENT_TR_ID vs TR_ACK_TR_ID (outstanding), then the SRC_*/DEST_*/
    # LEN_BYTES/*_VC descriptor for where the transfer was pointed.
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu0_cmd_buf_r — base: 0x03004000
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x10),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x18),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x20),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x28),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x30),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x38),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x40),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x48),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x50),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x58),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x60),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x68),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x70),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x78),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x80),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x88),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x90),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x98),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0xA0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0xA8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0xB0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0xB8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0xC0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0xC8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0xD0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0xD8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0xE0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0xE8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0xF0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0xF8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x100),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x108),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x110),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x118),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x120),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x128),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x130),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x138),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x140),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x148),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x150),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x158),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x160),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x168),
    "TT_ROCC_ACCEL_TT_ROCC_CPU0_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x170),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu1_cmd_buf_r — base: 0x03004C00
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0xC00),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0xC08),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0xC10),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0xC18),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0xC20),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0xC28),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0xC30),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0xC38),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0xC40),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0xC48),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0xC50),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0xC58),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0xC60),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0xC68),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0xC70),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0xC78),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0xC80),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0xC88),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0xC90),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0xC98),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0xCA0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0xCA8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0xCB0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0xCB8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0xCC0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0xCC8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0xCD0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0xCD8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0xCE0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0xCE8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0xCF0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0xCF8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0xD00),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0xD08),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0xD10),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0xD18),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0xD20),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0xD28),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0xD30),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0xD38),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0xD40),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0xD48),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0xD50),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0xD58),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0xD60),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0xD68),
    "TT_ROCC_ACCEL_TT_ROCC_CPU1_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0xD70),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu2_cmd_buf_r — base: 0x03005800
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x1800),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x1808),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x1810),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x1818),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x1820),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x1828),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x1830),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x1838),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x1840),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x1848),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x1850),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x1858),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x1860),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x1868),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x1870),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x1878),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x1880),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x1888),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x1890),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x1898),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x18A0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x18A8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x18B0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x18B8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x18C0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x18C8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x18D0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x18D8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x18E0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x18E8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x18F0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x18F8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x1900),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x1908),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x1910),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x1918),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x1920),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x1928),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x1930),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x1938),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x1940),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x1948),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x1950),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x1958),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x1960),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x1968),
    "TT_ROCC_ACCEL_TT_ROCC_CPU2_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x1970),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu3_cmd_buf_r — base: 0x03006400
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x2400),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x2408),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x2410),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x2418),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x2420),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x2428),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x2430),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x2438),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x2440),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x2448),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x2450),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x2458),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x2460),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x2468),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x2470),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x2478),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x2480),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x2488),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x2490),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x2498),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x24A0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x24A8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x24B0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x24B8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x24C0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x24C8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x24D0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x24D8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x24E0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x24E8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x24F0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x24F8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x2500),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x2508),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x2510),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x2518),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x2520),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x2528),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x2530),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x2538),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x2540),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x2548),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x2550),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x2558),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x2560),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x2568),
    "TT_ROCC_ACCEL_TT_ROCC_CPU3_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x2570),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu4_cmd_buf_r — base: 0x03007000
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x3000),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x3008),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x3010),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x3018),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x3020),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x3028),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x3030),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x3038),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x3040),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x3048),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x3050),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x3058),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x3060),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x3068),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x3070),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x3078),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x3080),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x3088),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x3090),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x3098),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x30A0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x30A8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x30B0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x30B8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x30C0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x30C8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x30D0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x30D8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x30E0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x30E8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x30F0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x30F8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x3100),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x3108),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x3110),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x3118),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x3120),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x3128),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x3130),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x3138),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x3140),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x3148),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x3150),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x3158),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x3160),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x3168),
    "TT_ROCC_ACCEL_TT_ROCC_CPU4_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x3170),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu5_cmd_buf_r — base: 0x03007C00
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x3C00),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x3C08),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x3C10),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x3C18),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x3C20),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x3C28),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x3C30),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x3C38),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x3C40),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x3C48),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x3C50),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x3C58),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x3C60),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x3C68),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x3C70),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x3C78),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x3C80),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x3C88),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x3C90),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x3C98),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x3CA0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x3CA8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x3CB0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x3CB8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x3CC0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x3CC8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x3CD0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x3CD8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x3CE0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x3CE8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x3CF0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x3CF8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x3D00),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x3D08),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x3D10),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x3D18),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x3D20),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x3D28),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x3D30),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x3D38),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x3D40),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x3D48),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x3D50),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x3D58),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x3D60),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x3D68),
    "TT_ROCC_ACCEL_TT_ROCC_CPU5_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x3D70),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu6_cmd_buf_r — base: 0x03008800
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x4800),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x4808),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x4810),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x4818),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x4820),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x4828),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x4830),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x4838),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x4840),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x4848),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x4850),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x4858),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x4860),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x4868),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x4870),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x4878),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x4880),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x4888),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x4890),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x4898),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x48A0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x48A8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x48B0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x48B8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x48C0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x48C8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x48D0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x48D8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x48E0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x48E8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x48F0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x48F8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x4900),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x4908),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x4910),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x4918),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x4920),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x4928),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x4930),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x4938),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x4940),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x4948),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x4950),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x4958),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x4960),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x4968),
    "TT_ROCC_ACCEL_TT_ROCC_CPU6_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x4970),
    # ---------------------------------------------------------------------------
    # tt_rocc_cpu7_cmd_buf_r — base: 0x03009400
    # ---------------------------------------------------------------------------
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_IE": RoccAcellRegisterDescription(offset=0x5400),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_IP": RoccAcellRegisterDescription(offset=0x5408),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_WR_SENT_TR_ID": RoccAcellRegisterDescription(offset=0x5410),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_TR_ACK_TR_ID": RoccAcellRegisterDescription(offset=0x5418),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SRC_ADDR": RoccAcellRegisterDescription(offset=0x5420),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SRC_BASE": RoccAcellRegisterDescription(offset=0x5428),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SRC_SIZE": RoccAcellRegisterDescription(offset=0x5430),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SRC_COORD": RoccAcellRegisterDescription(offset=0x5438),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_DEST_ADDR": RoccAcellRegisterDescription(offset=0x5440),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_DEST_BASE": RoccAcellRegisterDescription(offset=0x5448),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_DEST_SIZE": RoccAcellRegisterDescription(offset=0x5450),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_DEST_COORD": RoccAcellRegisterDescription(offset=0x5458),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_LEN_BYTES": RoccAcellRegisterDescription(offset=0x5460),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_REQ_VC": RoccAcellRegisterDescription(offset=0x5468),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_REQ_VC_BASE": RoccAcellRegisterDescription(offset=0x5470),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_REQ_VC_SIZE": RoccAcellRegisterDescription(offset=0x5478),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_RESP_VC": RoccAcellRegisterDescription(offset=0x5480),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_RESP_VC_BASE": RoccAcellRegisterDescription(offset=0x5488),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_RESP_VC_SIZE": RoccAcellRegisterDescription(offset=0x5490),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_TR_ID": RoccAcellRegisterDescription(offset=0x5498),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_TR_ID_BASE": RoccAcellRegisterDescription(offset=0x54A0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_TR_ID_SIZE": RoccAcellRegisterDescription(offset=0x54A8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_MCAST_EXCLUDE": RoccAcellRegisterDescription(offset=0x54B0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_LIST_ADDR": RoccAcellRegisterDescription(offset=0x54B8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_BASE_ADDR": RoccAcellRegisterDescription(offset=0x54C0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_INDEX": RoccAcellRegisterDescription(offset=0x54C8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_TIMES": RoccAcellRegisterDescription(offset=0x54D0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_ADDR_0_": RoccAcellRegisterDescription(offset=0x54D8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_ADDR_1_": RoccAcellRegisterDescription(offset=0x54E0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_ADDR_2_": RoccAcellRegisterDescription(offset=0x54E8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_SCATTER_ADDR_3_": RoccAcellRegisterDescription(offset=0x54F0),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_INLINE_DATA": RoccAcellRegisterDescription(offset=0x54F8),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_MAX_BYTES_IN_PACKET": RoccAcellRegisterDescription(offset=0x5500),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_MCAST_DESTS": RoccAcellRegisterDescription(offset=0x5508),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_L1_ACCUM_CFG": RoccAcellRegisterDescription(offset=0x5510),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_AXI_OPT_1": RoccAcellRegisterDescription(offset=0x5518),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_AXI_OPT_2": RoccAcellRegisterDescription(offset=0x5520),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_AUTOINC": RoccAcellRegisterDescription(offset=0x5528),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PACKET_TAGS": RoccAcellRegisterDescription(offset=0x5530),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_DEBUG": RoccAcellRegisterDescription(offset=0x5538),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_MISC": RoccAcellRegisterDescription(offset=0x5540),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IE_0": RoccAcellRegisterDescription(offset=0x5548),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IE_1": RoccAcellRegisterDescription(offset=0x5550),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IE_2": RoccAcellRegisterDescription(offset=0x5558),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IP_0": RoccAcellRegisterDescription(offset=0x5560),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IP_1": RoccAcellRegisterDescription(offset=0x5568),
    "TT_ROCC_ACCEL_TT_ROCC_CPU7_CMD_BUF_R_PER_TR_ID_IP_2": RoccAcellRegisterDescription(offset=0x5570),
    # ---------------------------------------------------------------------------
    # Debug Module APB registers (TT_DEBUG_MODULE_APB at 0x0300A000).
    # Offsets are relative to the DebugRegisterDescription base address 0x0300A000,
    # so each APB register offset = DMI_addr * 4.
    # ---------------------------------------------------------------------------
    "TT_DEBUG_MODULE_APB_DATA0": DebugRegisterDescription(offset=0x010),
    "TT_DEBUG_MODULE_APB_DATA1": DebugRegisterDescription(offset=0x014),
    "TT_DEBUG_MODULE_APB_DMCONTROL": DebugRegisterDescription(offset=0x040),
    "TT_DEBUG_MODULE_APB_DMSTATUS": DebugRegisterDescription(offset=0x044),
    "TT_DEBUG_MODULE_APB_HARTINFO": DebugRegisterDescription(offset=0x048),
    "TT_DEBUG_MODULE_APB_HALTSUMMARY1": DebugRegisterDescription(offset=0x04C),
    "TT_DEBUG_MODULE_APB_HAWINDOW": DebugRegisterDescription(offset=0x054),
    "TT_DEBUG_MODULE_APB_ABSTRACTCS": DebugRegisterDescription(offset=0x058),
    "TT_DEBUG_MODULE_APB_COMMAND": DebugRegisterDescription(offset=0x05C),
    "TT_DEBUG_MODULE_APB_ABSTRACTAUTO": DebugRegisterDescription(offset=0x060),
    "TT_DEBUG_MODULE_APB_PROGBUF0": DebugRegisterDescription(offset=0x080),
    "TT_DEBUG_MODULE_APB_PROGBUF1": DebugRegisterDescription(offset=0x084),
    "TT_DEBUG_MODULE_APB_STATUS2": DebugRegisterDescription(offset=0x0C8),
    "TT_DEBUG_MODULE_APB_SBCS": DebugRegisterDescription(offset=0x0E0),
    "TT_DEBUG_MODULE_APB_SBADDR0": DebugRegisterDescription(offset=0x0E4),
    "TT_DEBUG_MODULE_APB_SBADDR1": DebugRegisterDescription(offset=0x0E8),
    "TT_DEBUG_MODULE_APB_SBDATA0": DebugRegisterDescription(offset=0x0F0),
    "TT_DEBUG_MODULE_APB_SBDATA1": DebugRegisterDescription(offset=0x0F4),
    "TT_DEBUG_MODULE_APB_HALTSUMMARY0": DebugRegisterDescription(offset=0x100),
    # ---------------------------------------------------------------------------
    # SmnRegisterDescription registers
    # ---------------------------------------------------------------------------
    "SMN_RISC_RESET_REG": SmnRegisterDescription(offset=0x79B0),
    # ---------------------------------------------------------------------------
    # BusErrorUnitRegisterDescription — base address: 0x04000000
    #
    # Bus error units — one per Overlay CPU (unit0-unit7), unit stride 0x1000.
    # unit0 base 0x04000000 ... unit7 base 0x04007000. When a core takes a bad
    # bus/NOC access this latches the cause and offending physical address — the
    # first thing to check on a crash/hang (CAUSE != 0 means a fault was latched).
    #
    #   CAUSE        (+0x00): Error cause code (0 = no error).
    #   PHYS_ADDR    (+0x08): Physical address that faulted.
    #   ENABLE       (+0x10): Error-unit enable.
    #   PLIC_ENABLE  (+0x18): Route error to PLIC interrupt.
    #   ACCRUED      (+0x20): Accrued/sticky error bits.
    #   LOCAL_ENABLE (+0x28): Local (per-core) enable.
    # ---------------------------------------------------------------------------
    # bus_error_unit_0 — base: 0x04000000
    "BUS_ERROR_UNIT_0_CAUSE": BusErrorUnitRegisterDescription(offset=0x0),
    "BUS_ERROR_UNIT_0_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x8),
    "BUS_ERROR_UNIT_0_ENABLE": BusErrorUnitRegisterDescription(offset=0x10),
    "BUS_ERROR_UNIT_0_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x18),
    "BUS_ERROR_UNIT_0_ACCRUED": BusErrorUnitRegisterDescription(offset=0x20),
    "BUS_ERROR_UNIT_0_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x28),
    # bus_error_unit_1 — base: 0x04001000
    "BUS_ERROR_UNIT_1_CAUSE": BusErrorUnitRegisterDescription(offset=0x1000),
    "BUS_ERROR_UNIT_1_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x1008),
    "BUS_ERROR_UNIT_1_ENABLE": BusErrorUnitRegisterDescription(offset=0x1010),
    "BUS_ERROR_UNIT_1_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x1018),
    "BUS_ERROR_UNIT_1_ACCRUED": BusErrorUnitRegisterDescription(offset=0x1020),
    "BUS_ERROR_UNIT_1_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x1028),
    # bus_error_unit_2 — base: 0x04002000
    "BUS_ERROR_UNIT_2_CAUSE": BusErrorUnitRegisterDescription(offset=0x2000),
    "BUS_ERROR_UNIT_2_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x2008),
    "BUS_ERROR_UNIT_2_ENABLE": BusErrorUnitRegisterDescription(offset=0x2010),
    "BUS_ERROR_UNIT_2_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x2018),
    "BUS_ERROR_UNIT_2_ACCRUED": BusErrorUnitRegisterDescription(offset=0x2020),
    "BUS_ERROR_UNIT_2_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x2028),
    # bus_error_unit_3 — base: 0x04003000
    "BUS_ERROR_UNIT_3_CAUSE": BusErrorUnitRegisterDescription(offset=0x3000),
    "BUS_ERROR_UNIT_3_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x3008),
    "BUS_ERROR_UNIT_3_ENABLE": BusErrorUnitRegisterDescription(offset=0x3010),
    "BUS_ERROR_UNIT_3_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x3018),
    "BUS_ERROR_UNIT_3_ACCRUED": BusErrorUnitRegisterDescription(offset=0x3020),
    "BUS_ERROR_UNIT_3_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x3028),
    # bus_error_unit_4 — base: 0x04004000
    "BUS_ERROR_UNIT_4_CAUSE": BusErrorUnitRegisterDescription(offset=0x4000),
    "BUS_ERROR_UNIT_4_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x4008),
    "BUS_ERROR_UNIT_4_ENABLE": BusErrorUnitRegisterDescription(offset=0x4010),
    "BUS_ERROR_UNIT_4_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x4018),
    "BUS_ERROR_UNIT_4_ACCRUED": BusErrorUnitRegisterDescription(offset=0x4020),
    "BUS_ERROR_UNIT_4_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x4028),
    # bus_error_unit_5 — base: 0x04005000
    "BUS_ERROR_UNIT_5_CAUSE": BusErrorUnitRegisterDescription(offset=0x5000),
    "BUS_ERROR_UNIT_5_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x5008),
    "BUS_ERROR_UNIT_5_ENABLE": BusErrorUnitRegisterDescription(offset=0x5010),
    "BUS_ERROR_UNIT_5_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x5018),
    "BUS_ERROR_UNIT_5_ACCRUED": BusErrorUnitRegisterDescription(offset=0x5020),
    "BUS_ERROR_UNIT_5_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x5028),
    # bus_error_unit_6 — base: 0x04006000
    "BUS_ERROR_UNIT_6_CAUSE": BusErrorUnitRegisterDescription(offset=0x6000),
    "BUS_ERROR_UNIT_6_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x6008),
    "BUS_ERROR_UNIT_6_ENABLE": BusErrorUnitRegisterDescription(offset=0x6010),
    "BUS_ERROR_UNIT_6_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x6018),
    "BUS_ERROR_UNIT_6_ACCRUED": BusErrorUnitRegisterDescription(offset=0x6020),
    "BUS_ERROR_UNIT_6_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x6028),
    # bus_error_unit_7 — base: 0x04007000
    "BUS_ERROR_UNIT_7_CAUSE": BusErrorUnitRegisterDescription(offset=0x7000),
    "BUS_ERROR_UNIT_7_PHYS_ADDR": BusErrorUnitRegisterDescription(offset=0x7008),
    "BUS_ERROR_UNIT_7_ENABLE": BusErrorUnitRegisterDescription(offset=0x7010),
    "BUS_ERROR_UNIT_7_PLIC_ENABLE": BusErrorUnitRegisterDescription(offset=0x7018),
    "BUS_ERROR_UNIT_7_ACCRUED": BusErrorUnitRegisterDescription(offset=0x7020),
    "BUS_ERROR_UNIT_7_LOCAL_ENABLE": BusErrorUnitRegisterDescription(offset=0x7028),
    # ---------------------------------------------------------------------------
    # WatchdogTimerRegisterDescription — base address: 0x04008000
    #
    # Watchdog timers — one per Overlay CPU (core0-core7), core stride 0x1000.
    # core0 base 0x04008000 ... core7 base 0x0400F000. A tripped/near-zero
    # countdown points straight at which core stopped feeding the dog.
    #
    #   CTRL         (+0x00): Control/enable.
    #   COUNT        (+0x08): Current countdown value.
    #   SCALED_COUNT (+0x10): Scaled countdown value.
    #   FEED         (+0x18): Feed ("kick") register.
    #   KEY          (+0x1C): Access key.
    #   CMP          (+0x20): Compare/timeout threshold.
    # ---------------------------------------------------------------------------
    # tt_cluster_core0_wdt — base: 0x04008000
    "TT_CLUSTER_CORE0_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x0),
    "TT_CLUSTER_CORE0_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x8),
    "TT_CLUSTER_CORE0_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x10),
    "TT_CLUSTER_CORE0_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x18),
    "TT_CLUSTER_CORE0_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x1C),
    "TT_CLUSTER_CORE0_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x20),
    # tt_cluster_core1_wdt — base: 0x04009000
    "TT_CLUSTER_CORE1_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x1000),
    "TT_CLUSTER_CORE1_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x1008),
    "TT_CLUSTER_CORE1_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x1010),
    "TT_CLUSTER_CORE1_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x1018),
    "TT_CLUSTER_CORE1_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x101C),
    "TT_CLUSTER_CORE1_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x1020),
    # tt_cluster_core2_wdt — base: 0x0400A000
    "TT_CLUSTER_CORE2_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x2000),
    "TT_CLUSTER_CORE2_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x2008),
    "TT_CLUSTER_CORE2_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x2010),
    "TT_CLUSTER_CORE2_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x2018),
    "TT_CLUSTER_CORE2_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x201C),
    "TT_CLUSTER_CORE2_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x2020),
    # tt_cluster_core3_wdt — base: 0x0400B000
    "TT_CLUSTER_CORE3_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x3000),
    "TT_CLUSTER_CORE3_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x3008),
    "TT_CLUSTER_CORE3_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x3010),
    "TT_CLUSTER_CORE3_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x3018),
    "TT_CLUSTER_CORE3_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x301C),
    "TT_CLUSTER_CORE3_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x3020),
    # tt_cluster_core4_wdt — base: 0x0400C000
    "TT_CLUSTER_CORE4_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x4000),
    "TT_CLUSTER_CORE4_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x4008),
    "TT_CLUSTER_CORE4_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x4010),
    "TT_CLUSTER_CORE4_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x4018),
    "TT_CLUSTER_CORE4_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x401C),
    "TT_CLUSTER_CORE4_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x4020),
    # tt_cluster_core5_wdt — base: 0x0400D000
    "TT_CLUSTER_CORE5_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x5000),
    "TT_CLUSTER_CORE5_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x5008),
    "TT_CLUSTER_CORE5_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x5010),
    "TT_CLUSTER_CORE5_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x5018),
    "TT_CLUSTER_CORE5_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x501C),
    "TT_CLUSTER_CORE5_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x5020),
    # tt_cluster_core6_wdt — base: 0x0400E000
    "TT_CLUSTER_CORE6_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x6000),
    "TT_CLUSTER_CORE6_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x6008),
    "TT_CLUSTER_CORE6_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x6010),
    "TT_CLUSTER_CORE6_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x6018),
    "TT_CLUSTER_CORE6_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x601C),
    "TT_CLUSTER_CORE6_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x6020),
    # tt_cluster_core7_wdt — base: 0x0400F000
    "TT_CLUSTER_CORE7_WDT_CTRL": WatchdogTimerRegisterDescription(offset=0x7000),
    "TT_CLUSTER_CORE7_WDT_COUNT": WatchdogTimerRegisterDescription(offset=0x7008),
    "TT_CLUSTER_CORE7_WDT_SCALED_COUNT": WatchdogTimerRegisterDescription(offset=0x7010),
    "TT_CLUSTER_CORE7_WDT_FEED": WatchdogTimerRegisterDescription(offset=0x7018),
    "TT_CLUSTER_CORE7_WDT_KEY": WatchdogTimerRegisterDescription(offset=0x701C),
    "TT_CLUSTER_CORE7_WDT_CMP": WatchdogTimerRegisterDescription(offset=0x7020),
    # ---------------------------------------------------------------------------
    # ClintRegisterDescription — base address: 0x04020000
    #
    # CLINT (core-local interruptor): per-core machine software interrupt (MSIP)
    # and timer compare (MTIMECMP), plus the shared MTIME. MSIP_<core> != 0 means
    # a software interrupt is pending for that core.
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_CLINT_MSIP_0_": ClintRegisterDescription(offset=0x0),
    "TT_CLUSTER_CLINT_MSIP_1_": ClintRegisterDescription(offset=0x4),
    "TT_CLUSTER_CLINT_MSIP_2_": ClintRegisterDescription(offset=0x8),
    "TT_CLUSTER_CLINT_MSIP_3_": ClintRegisterDescription(offset=0xC),
    "TT_CLUSTER_CLINT_MSIP_4_": ClintRegisterDescription(offset=0x10),
    "TT_CLUSTER_CLINT_MSIP_5_": ClintRegisterDescription(offset=0x14),
    "TT_CLUSTER_CLINT_MSIP_6_": ClintRegisterDescription(offset=0x18),
    "TT_CLUSTER_CLINT_MSIP_7_": ClintRegisterDescription(offset=0x1C),
    "TT_CLUSTER_CLINT_MTIMECMP_0_": ClintRegisterDescription(offset=0x4000),
    "TT_CLUSTER_CLINT_MTIMECMP_1_": ClintRegisterDescription(offset=0x4008),
    "TT_CLUSTER_CLINT_MTIMECMP_2_": ClintRegisterDescription(offset=0x4010),
    "TT_CLUSTER_CLINT_MTIMECMP_3_": ClintRegisterDescription(offset=0x4018),
    "TT_CLUSTER_CLINT_MTIMECMP_4_": ClintRegisterDescription(offset=0x4020),
    "TT_CLUSTER_CLINT_MTIMECMP_5_": ClintRegisterDescription(offset=0x4028),
    "TT_CLUSTER_CLINT_MTIMECMP_6_": ClintRegisterDescription(offset=0x4030),
    "TT_CLUSTER_CLINT_MTIMECMP_7_": ClintRegisterDescription(offset=0x4038),
    "TT_CLUSTER_CLINT_MTIME": ClintRegisterDescription(offset=0xBFF8),
    # ---------------------------------------------------------------------------
    # PlicRegisterDescription — base address: 0x08000000
    #
    # PLIC (platform-level interrupt controller): PRIORITY_<n> per-source priority,
    # PENDING_<n> pending bitmap words, and per-core (core0-core7) IE_0/1/2 enable
    # words, THRESHOLD, and CLAIM_COMPLETE. Explains which interrupt is (not) firing.
    # ---------------------------------------------------------------------------
    "TT_CLUSTER_PLIC_PRIORITY_0_": PlicRegisterDescription(offset=0x4),
    "TT_CLUSTER_PLIC_PRIORITY_1_": PlicRegisterDescription(offset=0x8),
    "TT_CLUSTER_PLIC_PRIORITY_2_": PlicRegisterDescription(offset=0xC),
    "TT_CLUSTER_PLIC_PRIORITY_3_": PlicRegisterDescription(offset=0x10),
    "TT_CLUSTER_PLIC_PRIORITY_4_": PlicRegisterDescription(offset=0x14),
    "TT_CLUSTER_PLIC_PRIORITY_5_": PlicRegisterDescription(offset=0x18),
    "TT_CLUSTER_PLIC_PRIORITY_6_": PlicRegisterDescription(offset=0x1C),
    "TT_CLUSTER_PLIC_PRIORITY_7_": PlicRegisterDescription(offset=0x20),
    "TT_CLUSTER_PLIC_PRIORITY_8_": PlicRegisterDescription(offset=0x24),
    "TT_CLUSTER_PLIC_PRIORITY_9_": PlicRegisterDescription(offset=0x28),
    "TT_CLUSTER_PLIC_PRIORITY_10_": PlicRegisterDescription(offset=0x2C),
    "TT_CLUSTER_PLIC_PRIORITY_11_": PlicRegisterDescription(offset=0x30),
    "TT_CLUSTER_PLIC_PRIORITY_12_": PlicRegisterDescription(offset=0x34),
    "TT_CLUSTER_PLIC_PRIORITY_13_": PlicRegisterDescription(offset=0x38),
    "TT_CLUSTER_PLIC_PRIORITY_14_": PlicRegisterDescription(offset=0x3C),
    "TT_CLUSTER_PLIC_PRIORITY_15_": PlicRegisterDescription(offset=0x40),
    "TT_CLUSTER_PLIC_PRIORITY_16_": PlicRegisterDescription(offset=0x44),
    "TT_CLUSTER_PLIC_PRIORITY_17_": PlicRegisterDescription(offset=0x48),
    "TT_CLUSTER_PLIC_PRIORITY_18_": PlicRegisterDescription(offset=0x4C),
    "TT_CLUSTER_PLIC_PRIORITY_19_": PlicRegisterDescription(offset=0x50),
    "TT_CLUSTER_PLIC_PRIORITY_20_": PlicRegisterDescription(offset=0x54),
    "TT_CLUSTER_PLIC_PRIORITY_21_": PlicRegisterDescription(offset=0x58),
    "TT_CLUSTER_PLIC_PRIORITY_22_": PlicRegisterDescription(offset=0x5C),
    "TT_CLUSTER_PLIC_PRIORITY_23_": PlicRegisterDescription(offset=0x60),
    "TT_CLUSTER_PLIC_PRIORITY_24_": PlicRegisterDescription(offset=0x64),
    "TT_CLUSTER_PLIC_PRIORITY_25_": PlicRegisterDescription(offset=0x68),
    "TT_CLUSTER_PLIC_PRIORITY_26_": PlicRegisterDescription(offset=0x6C),
    "TT_CLUSTER_PLIC_PRIORITY_27_": PlicRegisterDescription(offset=0x70),
    "TT_CLUSTER_PLIC_PRIORITY_28_": PlicRegisterDescription(offset=0x74),
    "TT_CLUSTER_PLIC_PRIORITY_29_": PlicRegisterDescription(offset=0x78),
    "TT_CLUSTER_PLIC_PRIORITY_30_": PlicRegisterDescription(offset=0x7C),
    "TT_CLUSTER_PLIC_PRIORITY_31_": PlicRegisterDescription(offset=0x80),
    "TT_CLUSTER_PLIC_PRIORITY_32_": PlicRegisterDescription(offset=0x84),
    "TT_CLUSTER_PLIC_PRIORITY_33_": PlicRegisterDescription(offset=0x88),
    "TT_CLUSTER_PLIC_PRIORITY_34_": PlicRegisterDescription(offset=0x8C),
    "TT_CLUSTER_PLIC_PRIORITY_35_": PlicRegisterDescription(offset=0x90),
    "TT_CLUSTER_PLIC_PRIORITY_36_": PlicRegisterDescription(offset=0x94),
    "TT_CLUSTER_PLIC_PRIORITY_37_": PlicRegisterDescription(offset=0x98),
    "TT_CLUSTER_PLIC_PRIORITY_38_": PlicRegisterDescription(offset=0x9C),
    "TT_CLUSTER_PLIC_PRIORITY_39_": PlicRegisterDescription(offset=0xA0),
    "TT_CLUSTER_PLIC_PRIORITY_40_": PlicRegisterDescription(offset=0xA4),
    "TT_CLUSTER_PLIC_PRIORITY_41_": PlicRegisterDescription(offset=0xA8),
    "TT_CLUSTER_PLIC_PRIORITY_42_": PlicRegisterDescription(offset=0xAC),
    "TT_CLUSTER_PLIC_PRIORITY_43_": PlicRegisterDescription(offset=0xB0),
    "TT_CLUSTER_PLIC_PRIORITY_44_": PlicRegisterDescription(offset=0xB4),
    "TT_CLUSTER_PLIC_PRIORITY_45_": PlicRegisterDescription(offset=0xB8),
    "TT_CLUSTER_PLIC_PRIORITY_46_": PlicRegisterDescription(offset=0xBC),
    "TT_CLUSTER_PLIC_PRIORITY_47_": PlicRegisterDescription(offset=0xC0),
    "TT_CLUSTER_PLIC_PRIORITY_48_": PlicRegisterDescription(offset=0xC4),
    "TT_CLUSTER_PLIC_PRIORITY_49_": PlicRegisterDescription(offset=0xC8),
    "TT_CLUSTER_PLIC_PRIORITY_50_": PlicRegisterDescription(offset=0xCC),
    "TT_CLUSTER_PLIC_PRIORITY_51_": PlicRegisterDescription(offset=0xD0),
    "TT_CLUSTER_PLIC_PRIORITY_52_": PlicRegisterDescription(offset=0xD4),
    "TT_CLUSTER_PLIC_PRIORITY_53_": PlicRegisterDescription(offset=0xD8),
    "TT_CLUSTER_PLIC_PRIORITY_54_": PlicRegisterDescription(offset=0xDC),
    "TT_CLUSTER_PLIC_PRIORITY_55_": PlicRegisterDescription(offset=0xE0),
    "TT_CLUSTER_PLIC_PRIORITY_56_": PlicRegisterDescription(offset=0xE4),
    "TT_CLUSTER_PLIC_PRIORITY_57_": PlicRegisterDescription(offset=0xE8),
    "TT_CLUSTER_PLIC_PRIORITY_58_": PlicRegisterDescription(offset=0xEC),
    "TT_CLUSTER_PLIC_PRIORITY_59_": PlicRegisterDescription(offset=0xF0),
    "TT_CLUSTER_PLIC_PRIORITY_60_": PlicRegisterDescription(offset=0xF4),
    "TT_CLUSTER_PLIC_PRIORITY_61_": PlicRegisterDescription(offset=0xF8),
    "TT_CLUSTER_PLIC_PRIORITY_62_": PlicRegisterDescription(offset=0xFC),
    "TT_CLUSTER_PLIC_PRIORITY_63_": PlicRegisterDescription(offset=0x100),
    "TT_CLUSTER_PLIC_PRIORITY_64_": PlicRegisterDescription(offset=0x104),
    "TT_CLUSTER_PLIC_PRIORITY_65_": PlicRegisterDescription(offset=0x108),
    "TT_CLUSTER_PLIC_PRIORITY_66_": PlicRegisterDescription(offset=0x10C),
    "TT_CLUSTER_PLIC_PRIORITY_67_": PlicRegisterDescription(offset=0x110),
    "TT_CLUSTER_PLIC_PRIORITY_68_": PlicRegisterDescription(offset=0x114),
    "TT_CLUSTER_PLIC_PRIORITY_69_": PlicRegisterDescription(offset=0x118),
    "TT_CLUSTER_PLIC_PRIORITY_70_": PlicRegisterDescription(offset=0x11C),
    "TT_CLUSTER_PLIC_PRIORITY_71_": PlicRegisterDescription(offset=0x120),
    "TT_CLUSTER_PLIC_PRIORITY_72_": PlicRegisterDescription(offset=0x124),
    "TT_CLUSTER_PLIC_PRIORITY_73_": PlicRegisterDescription(offset=0x128),
    "TT_CLUSTER_PLIC_PRIORITY_74_": PlicRegisterDescription(offset=0x12C),
    "TT_CLUSTER_PLIC_PRIORITY_75_": PlicRegisterDescription(offset=0x130),
    "TT_CLUSTER_PLIC_PRIORITY_76_": PlicRegisterDescription(offset=0x134),
    "TT_CLUSTER_PLIC_PRIORITY_77_": PlicRegisterDescription(offset=0x138),
    "TT_CLUSTER_PLIC_PRIORITY_78_": PlicRegisterDescription(offset=0x13C),
    "TT_CLUSTER_PLIC_PRIORITY_79_": PlicRegisterDescription(offset=0x140),
    "TT_CLUSTER_PLIC_PENDING_0_": PlicRegisterDescription(offset=0x1000),
    "TT_CLUSTER_PLIC_PENDING_1_": PlicRegisterDescription(offset=0x1004),
    "TT_CLUSTER_PLIC_PENDING_2_": PlicRegisterDescription(offset=0x1008),
    "TT_CLUSTER_PLIC_CORE0_IE_0_": PlicRegisterDescription(offset=0x2000),
    "TT_CLUSTER_PLIC_CORE0_IE_1_": PlicRegisterDescription(offset=0x2004),
    "TT_CLUSTER_PLIC_CORE0_IE_2_": PlicRegisterDescription(offset=0x2008),
    "TT_CLUSTER_PLIC_CORE1_IE_0_": PlicRegisterDescription(offset=0x2080),
    "TT_CLUSTER_PLIC_CORE1_IE_1_": PlicRegisterDescription(offset=0x2084),
    "TT_CLUSTER_PLIC_CORE1_IE_2_": PlicRegisterDescription(offset=0x2088),
    "TT_CLUSTER_PLIC_CORE2_IE_0_": PlicRegisterDescription(offset=0x2100),
    "TT_CLUSTER_PLIC_CORE2_IE_1_": PlicRegisterDescription(offset=0x2104),
    "TT_CLUSTER_PLIC_CORE2_IE_2_": PlicRegisterDescription(offset=0x2108),
    "TT_CLUSTER_PLIC_CORE3_IE_0_": PlicRegisterDescription(offset=0x2180),
    "TT_CLUSTER_PLIC_CORE3_IE_1_": PlicRegisterDescription(offset=0x2184),
    "TT_CLUSTER_PLIC_CORE3_IE_2_": PlicRegisterDescription(offset=0x2188),
    "TT_CLUSTER_PLIC_CORE4_IE_0_": PlicRegisterDescription(offset=0x2200),
    "TT_CLUSTER_PLIC_CORE4_IE_1_": PlicRegisterDescription(offset=0x2204),
    "TT_CLUSTER_PLIC_CORE4_IE_2_": PlicRegisterDescription(offset=0x2208),
    "TT_CLUSTER_PLIC_CORE5_IE_0_": PlicRegisterDescription(offset=0x2280),
    "TT_CLUSTER_PLIC_CORE5_IE_1_": PlicRegisterDescription(offset=0x2284),
    "TT_CLUSTER_PLIC_CORE5_IE_2_": PlicRegisterDescription(offset=0x2288),
    "TT_CLUSTER_PLIC_CORE6_IE_0_": PlicRegisterDescription(offset=0x2300),
    "TT_CLUSTER_PLIC_CORE6_IE_1_": PlicRegisterDescription(offset=0x2304),
    "TT_CLUSTER_PLIC_CORE6_IE_2_": PlicRegisterDescription(offset=0x2308),
    "TT_CLUSTER_PLIC_CORE7_IE_0_": PlicRegisterDescription(offset=0x2380),
    "TT_CLUSTER_PLIC_CORE7_IE_1_": PlicRegisterDescription(offset=0x2384),
    "TT_CLUSTER_PLIC_CORE7_IE_2_": PlicRegisterDescription(offset=0x2388),
    "TT_CLUSTER_PLIC_CORE0_THRESHOLD": PlicRegisterDescription(offset=0x200000),
    "TT_CLUSTER_PLIC_CORE0_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x200004),
    "TT_CLUSTER_PLIC_CORE1_THRESHOLD": PlicRegisterDescription(offset=0x201000),
    "TT_CLUSTER_PLIC_CORE1_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x201004),
    "TT_CLUSTER_PLIC_CORE2_THRESHOLD": PlicRegisterDescription(offset=0x202000),
    "TT_CLUSTER_PLIC_CORE2_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x202004),
    "TT_CLUSTER_PLIC_CORE3_THRESHOLD": PlicRegisterDescription(offset=0x203000),
    "TT_CLUSTER_PLIC_CORE3_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x203004),
    "TT_CLUSTER_PLIC_CORE4_THRESHOLD": PlicRegisterDescription(offset=0x204000),
    "TT_CLUSTER_PLIC_CORE4_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x204004),
    "TT_CLUSTER_PLIC_CORE5_THRESHOLD": PlicRegisterDescription(offset=0x205000),
    "TT_CLUSTER_PLIC_CORE5_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x205004),
    "TT_CLUSTER_PLIC_CORE6_THRESHOLD": PlicRegisterDescription(offset=0x206000),
    "TT_CLUSTER_PLIC_CORE6_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x206004),
    "TT_CLUSTER_PLIC_CORE7_THRESHOLD": PlicRegisterDescription(offset=0x207000),
    "TT_CLUSTER_PLIC_CORE7_CLAIM_COMPLETE": PlicRegisterDescription(offset=0x207004),
}
