from dbd.tt_object import TTObject, TTObjectSet
import tt_util as util
from tt_graph import Queue, Op
import tt_device

command_metadata = {
        "short" : "st",
        "expected_argument_count" : 0,
        "arguments_description" : ": Test debuda internals"
    }

def test_object():
    class my_tt_obj(TTObject):
        pass

    oset1 = TTObjectSet()
    oset2 = TTObjectSet()

    for i in range (15):
        o = my_tt_obj()
        o._id = i
        if i <= 10: oset1.add (o)
        if i >= 5:  oset2.add (o)

    odiff = oset1-oset2
    print (type(odiff))

    oset3 = oset1.copy()
    print (f"oset3 == oset1: {oset3 == oset1}")

    elem = oset2.first()
    print (elem)
    assert elem in oset1
    assert elem in oset3
    oset1.delete (lambda x: x == elem)
    assert elem not in oset1
    assert elem in oset3
    oset1.compare (oset3)
    oset3.keep (lambda x: x == elem)

    print (oset2.find_id(elem.id()))
    assert oset2.find_id(-1) is None
    util.INFO (f"test_object: PASS")

def test_fanin_fanout_queue_op_level(context):
    graph = context.netlist.graphs.first()
    for fop in graph.ops:
        print (f"{fop} fanin: {graph.get_fanin(fop)}")
        print (f"{fop} fanout: {graph.get_fanout(fop)}")

    for fq in graph.queues:
        print (f"{fq} fanin: {graph.get_fanin(fq)}")
        print (f"{fq} fanout: {graph.get_fanout(fq)}")

    util.INFO (f"test_fanin_fanout: PASS")

def test_fanin_fanout_buffer_level(context):
    graph = context.netlist.graphs.first()
    for fop in graph.ops:
        op_buffers = graph.get_buffers (fop)
        print (f"test_fanin_fanout_buffer_level for {fop}")
        dest_buffers = op_buffers.copy()
        dest_buffers.keep (graph.is_dest_buffer)
        for buffer in dest_buffers:
            buffer_fanins = graph.get_fanin(buffer)
            print (f"{buffer} buffer fanin: {buffer_fanins}")

        src_buffers = op_buffers.copy()
        src_buffers.keep (graph.is_src_buffer)
        for buffer in src_buffers:
            buffer_fanouts = graph.get_fanout(buffer)
            print (f"{buffer} buffer fanout: {buffer_fanouts}")

        print (f"Pipes for buffer: {graph.get_pipes (src_buffers)}")

def run(args, context, ui_state = None):
    navigation_suggestions = []
    test_object ()
    test_fanin_fanout_queue_op_level (context)
    test_fanin_fanout_buffer_level (context)
    return navigation_suggestions
