# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Shared DWARF expression evaluator for both DIE location expressions and CFI register rules.

This module provides a unified expression evaluation engine that can be used by:
- Variable location expressions (DW_AT_location in DIEs)
- CFI register recovery rules (EXPRESSION/VAL_EXPRESSION in FDEs)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from elftools.dwarf.dwarf_expr import DWARFExprOp
from elftools.dwarf.locationlists import LocationExpr
import ttexalens.util as util

if TYPE_CHECKING:
    from ttexalens.elf.cu import ElfCompileUnit
    from ttexalens.elf.frame import FrameInspection


def evaluate_dwarf_expression(
    parsed_expression: list[DWARFExprOp],
    frame_inspection: FrameInspection | None = None,
    cfa: int | None = None,
    cu: "ElfCompileUnit | None" = None,
) -> tuple[bool, Any | None]:
    """
    Evaluate a DWARF expression and return (is_address, value).

    Args:
        parsed_expression: List of DWARF expression operations to evaluate
        frame_inspection: Frame context for register reads and memory access
        cfa: Call Frame Address for DW_OP_call_frame_cfa operations
        cu: Compile Unit for operations that need DIE lookups (optional)

    Returns:
        (is_address, value): Tuple where:
            - is_address: True if value is a memory address, False if direct value
            - value: The evaluated result (int, bytes, or None on error)
    """
    from ttexalens.elf.variable import ElfVariable
    from ttexalens.memory_access import FixedMemoryAccess

    util.DEBUG(f"   {parsed_expression}")

    is_address = False
    value = None
    stack = []

    for op in parsed_expression:
        if op.op_name == "DW_OP_fbreg":
            # Frame base relative addressing
            # This requires finding the function's frame_base attribute
            if cu is None:
                util.DEBUG(f"DW_OP_fbreg requires CU context")
                return False, None

            # Note: In CFI context, we might not have DIE context, so this may fail
            # For CFI expressions, DW_OP_call_frame_cfa is more common
            util.DEBUG(f"DW_OP_fbreg not fully supported without DIE context")
            return False, None

        elif op.op_name == "DW_OP_call_frame_cfa":
            if cfa is None:
                if frame_inspection is not None and hasattr(frame_inspection, "cfa"):
                    value = frame_inspection.cfa
                else:
                    return False, None
            else:
                value = cfa
            is_address = True

        elif op.op_name == "DW_OP_entry_value":
            if len(op.args) != 1 or not isinstance(op.args[0], list):
                return False, None
            parsed_sub_expression = op.args[0]
            _, value = evaluate_dwarf_expression(parsed_sub_expression, frame_inspection, cfa, cu)
            if value is None:
                return False, None
            stack.append(value)

        elif op.op_name == "DW_OP_regval_type":
            if len(op.args) != 2:
                return False, None
            if cu is None or frame_inspection is None:
                return False, None
            register_index = op.args[0]
            type_die_offset = op.args[1]
            type_die = cu.find_DIE_at_local_offset(type_die_offset)
            if type_die is None:
                return False, None
            register_value = frame_inspection.read_register(register_index)
            if register_value is None:
                return False, None
            type_size = type_die.size if type_die.size is not None else 4
            value = ElfVariable(
                type_die, 0, FixedMemoryAccess(register_value.to_bytes(type_size, byteorder="little"))
            ).read_value()
            is_address = False

        elif op.op_name == "DW_OP_convert" or op.op_name == "DW_OP_reinterpret":
            if len(op.args) != 1:
                return False, None
            type_die_offset = op.args[0]
            if type_die_offset != 0:
                if cu is None or len(stack) == 0:
                    return False, None
                stack_value = stack.pop()
                type_die = cu.find_DIE_at_local_offset(type_die_offset)
                if type_die is None:
                    return False, None
                type_size = type_die.size if type_die.size is not None else 4
                value = ElfVariable(
                    type_die, 0, FixedMemoryAccess(stack_value.to_bytes(type_size, byteorder="little"))
                ).read_value()
                stack.append(value)
            else:
                # Generic type conversion, we can ignore it
                pass

        elif op.op_name == "DW_OP_stack_value":
            if len(stack) == 0:
                return False, value
            return False, stack.pop()

        elif op.op_name == "DW_OP_regx":
            if len(op.args) != 1 or not isinstance(op.args[0], int):
                return False, None
            register_index = op.args[0]
            if frame_inspection is None:
                return False, None
            value = frame_inspection.read_register(register_index)
            if value is None:
                return False, None
            is_address = False

        elif op.op_name.startswith("DW_OP_reg"):
            register_index = int(op.op_name[len("DW_OP_reg") :])
            if frame_inspection is None:
                return False, None
            value = frame_inspection.read_register(register_index)
            if value is None:
                return False, None
            is_address = False

        elif op.op_name == "DW_OP_bregx":
            if len(op.args) != 2 or not isinstance(op.args[0], int) or not isinstance(op.args[1], int):
                return False, None
            register_index = op.args[0]
            if frame_inspection is None:
                return False, None
            register_value = frame_inspection.read_register(register_index)
            if register_value is None:
                return False, None
            value = register_value + op.args[1]
            is_address = True

        elif op.op_name.startswith("DW_OP_breg"):
            register_index = int(op.op_name[len("DW_OP_breg") :])
            if frame_inspection is None:
                return False, None
            register_value = frame_inspection.read_register(register_index)
            if register_value is None:
                return False, None
            if len(op.args) != 1 or not isinstance(op.args[0], int):
                return False, None
            value = register_value + op.args[0]
            is_address = True

        elif op.op_name == "DW_OP_addr":
            if len(op.args) != 1 or not isinstance(op.args[0], int):
                return False, None
            value = op.args[0]
            is_address = True

        elif op.op_name == "DW_OP_deref":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            try:
                read_address = int(value)
            except:
                return False, None
            if frame_inspection is None:
                return False, None
            value = frame_inspection.mem_access.read_word(read_address)  # Default to 4 bytes as generic type
            is_address = False

        elif op.op_name == "DW_OP_const_type":
            if (
                len(op.args) != 2
                or not isinstance(op.args[0], int)
                or (not isinstance(op.args[1], list) and not isinstance(op.args[1], bytes))
            ):
                return False, None
            if cu is None:
                return False, None
            type_die_offset = op.args[0]
            type_die = cu.find_DIE_at_local_offset(type_die_offset)
            if type_die is None:
                return False, None
            const_value = op.args[1]
            if isinstance(const_value, list):
                const_value = bytes(const_value)
            value = ElfVariable(type_die, 0, FixedMemoryAccess(const_value)).read_value()
            is_address = False

        elif (
            op.op_name == "DW_OP_const1u"
            or op.op_name == "DW_OP_const1s"
            or op.op_name == "DW_OP_const2u"
            or op.op_name == "DW_OP_const2s"
            or op.op_name == "DW_OP_const4u"
            or op.op_name == "DW_OP_const4s"
            or op.op_name == "DW_OP_const8u"
            or op.op_name == "DW_OP_const8s"
            or op.op_name == "DW_OP_constu"
            or op.op_name == "DW_OP_consts"
        ):
            if len(op.args) != 1 or not isinstance(op.args[0], int):
                return False, None
            value = op.args[0]
            is_address = False

        elif op.op_name == "DW_OP_dup":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            stack.append(value)
            stack.append(value)

        elif op.op_name == "DW_OP_drop":
            if len(stack) > 0:
                stack.pop()
            else:
                if value is None:
                    return False, None
                value = None

        elif op.op_name == "DW_OP_over":
            if len(stack) < 2:
                return False, None
            stack.append(stack[-2])

        elif op.op_name == "DW_OP_pick":
            if len(op.args) != 1 or not isinstance(op.args[0], int):
                return False, None
            index = op.args[0]
            if index == 0:
                if len(stack) > 0:
                    value = stack.pop()
                if value is None:
                    return False, None
                stack.append(value)
                stack.append(value)
            else:
                if len(stack) < index + 1:
                    return False, None
                stack.append(stack[-index - 1])

        elif op.op_name == "DW_OP_swap":
            if len(stack) < 2:
                return False, None
            v1 = stack[-1]
            v2 = stack[-2]
            stack[-1] = v2
            stack[-2] = v1

        elif op.op_name == "DW_OP_rot":
            if len(stack) < 3:
                return False, None
            v1 = stack[-1]
            v2 = stack[-2]
            v3 = stack[-3]
            stack[-1] = v2
            stack[-2] = v3
            stack[-3] = v1

        elif op.op_name == "DW_OP_xderef":
            if len(stack) < 2:
                return False, None
            address = stack.pop()
            address_space_id = stack.pop()  # TODO: Does our architecture support multiple address spaces?
            if frame_inspection is None:
                return False, None
            value = frame_inspection.mem_access.read_word(address)  # Default to 4 bytes as generic type
            is_address = False

        elif op.op_name == "DW_OP_abs":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            try:
                value = abs(int(value))
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_neg":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            try:
                value = -value
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_not":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            try:
                value = not bool(value)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_and":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = int(arg2) & int(arg1)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_div":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = int(arg2) // int(arg1)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_minus":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = int(arg2) - int(arg1)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_mod":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = int(arg2) % int(arg1)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_mul":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 * arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_or":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 | arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_plus":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 + arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_plus_uconst":
            if len(stack) > 0:
                value = stack.pop()
            if value is None:
                return False, None
            if len(op.args) != 1:
                return False, None
            try:
                value = value + op.args[0]
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_shl":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 << arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_shr":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 >> arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_shra":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 // (2**arg1)
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_xor":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = arg2 ^ arg1
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_eq":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 == arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_ge":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 >= arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_gt":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 > arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_le":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 <= arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_lt":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 < arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_ne":
            if len(stack) < 2:
                return False, None
            arg1 = stack.pop()
            arg2 = stack.pop()
            try:
                value = 1 if arg2 != arg1 else 0
                stack.append(value)
            except:
                return False, None

        elif op.op_name == "DW_OP_call2" or op.op_name == "DW_OP_call4" or op.op_name == "DW_OP_call_ref":
            # These require DIE lookups and are complex
            if cu is None:
                util.DEBUG(f"{op.op_name} requires CU context")
                return False, None
            # Would need to implement full call semantics
            util.DEBUG(f"{op.op_name} not fully implemented in CFI context")
            return False, None

        elif op.op_name.startswith("DW_OP_lit"):
            literal_value = int(op.op_name[len("DW_OP_lit") :])
            stack.append(literal_value)

        else:
            # Unsupported operation
            util.DEBUG(f"Unsupported DWARF location operation: {op.op_name}")
            return False, None

    if value is None and len(stack) > 0:
        value = stack.pop()
    return is_address, value
