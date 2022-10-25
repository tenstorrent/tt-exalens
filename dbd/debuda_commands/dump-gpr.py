"""Prints all RISC-V registers for TRISC0, TRISC1, TRISC2 and Brisc on current core.
If the core cannot be paused(halted), it prints nothing. If core is not active, an exception is thrown.

.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 > gpr
        Register     Brisc    Trisc0      Trisc1      Trisc2
        -----------  -------  ----------  ----------  ----------
        0 - zero     -        0x00000000  0x00000000  0x00000000
        1 - ra       -        0x0000d208  0x00012208  0x00015208
        2 - sp       -        0xffb00400  0xffb00100  0xffb006c0
        3 - gp       -        0xffb00800  0xffb00800  0xffb00880
        4 - tp       -        0x00000000  0x00000000  0x00000000
        5 - t0       -        0xffe40000  0x00000000  0x000151bc
        6 - t1       -        0xffef0000  0xb20102c0  0x0001a080
        ...

"""
import tabulate
from tt_debug_risc import RiscDebug, RiscLoc

command_metadata = {
    "short" : "gpr",
    "type" : "low-level",
    "expected_argument_count" : [ 0 ],
    "arguments" : "",
    "description" : "Prints general purpose registers at Risc cores."
}
RISC_REGS = {
    0:'zero', 1:'ra', 2:'sp', 3:'gp', 4:'tp', 5:'t0', 6:'t1', 7:'t2', 8:'s0 / fp', 9:'s1', 10:'a0', 11:'a1', 12:'a2',
    13:'a3', 14:'a4', 15:'a5', 16:'a6', 17:'a7', 18:'s2', 19:'s3', 20:'s4', 21:'s5', 22:'s6', 23:'s7', 24:'s8', 25:'s9',
    26:'s10', 27:'s11', 28:'t3', 29:'t4', 30:'t5', 31:'t6', 32:'PC'}

def run(args, context, ui_state = None):
    result = {}
    device_id = ui_state['current_device_id']
    x = ui_state['current_x']
    y = ui_state['current_y']
    for i in range(0,4):
        risc = RiscDebug(RiscLoc(device_id, x, y, 0, i))
        risc.enable_debug()
        risc.pause()
        if risc.is_paused():
            result[i]={}
            for j in range(0,33):
                reg_val = risc.read_gpr(j)
                result[i][j] = reg_val
            risc.contnue()


    table=[]
    for i in range(0,33):
        row = [f"{i} - {RISC_REGS[i]}"]
        for j in range(0,4):
            row.append(f"0x{result[j][i]:08x}" if j in result else '-')
        table.append(row)
    if len(table) > 0:
        print (tabulate.tabulate(table, headers=["Register", "Brisc", "Trisc0", "Trisc1", "Trisc2" ] ))

    return []