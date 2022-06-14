#!/usr/bin/env python3
import argparse, tapout_sweep, yaml
import traceback
import os

# /home/macimovic/work/budabackend/verif/graph_tests/netlists/netlist_bert_mha_train.yaml
# /home/macimovic/work/budabackend/verif/directed_tests/netlist_bert_encoder_train_multi_core.yaml

SECTION_QUEUES = "queues:"
SECTION_PROGRAMS = "programs:"
SECTION_GRAPHS = "graphs:"

tapout = None

trace_enabled = False
def trace(s):
    global trace_enabled
    if (trace_enabled):
        print(s)


# gets graph name for provided operation
def get_graph_name(nl, operation_name):
    for graph_name in get_graph_names(nl):
        if operation_name in get_graph(nl, graph_name):
            return graph_name
    raise Exception(f"Graph for {operation_name} not found")

def get_graph(nl, graph_name):
    return nl["graphs"][graph_name]

def get_graph_from_op(nl, operation):
    return get_graph(nl, get_graph_name(nl, operation))

def get_graph_names(nl):
    return [graph_name for graph_name in nl["graphs"]]

def get_queue_names(nl):
    return [queue_name for queue_name in nl["queues"]]

def get_queue(nl, q_name):
    return nl["queues"][q_name]

def set_queue_input(nl, q_name, input_name):
    get_queue(nl, q_name)["input"] = input_name

def get_queue_input(nl, q_name):
    return get_queue(nl, q_name)["input"]

def get_op_names(nl, graph_name):
    result = []
    for op in get_graph(nl, graph_name):
        if isinstance(nl["graphs"][graph_name][op], dict):
            result.append(op)
    return result

def get_op(nl, operation):
    return get_graph_from_op(nl, operation)[operation]

def set_op_inputs(nl, op_name, inputs):
    get_op(nl, op_name)["inputs"] = inputs

def get_op_inputs(nl, operation):
    return get_op(nl, operation)["inputs"]

def del_op(nl, op_name):
    trace("del op:" + op_name)
    g = get_graph_from_op(nl, op_name)
    del g[op_name]

def del_queue(nl, q_name):
    trace("del queue:" + q_name)
    del nl["queues"][q_name]

def del_graph(nl, graph_name):
    trace("del graph:"+graph_name)
    del nl["graphs"][graph_name]

# for a given netlist and list of operations
# returns graph name and checks whether
# all operations are part of graph
def get_graph_name_from_list(nl, operations):
    graph_name = ""
    for op in operations:
        if not graph_name:
            graph_name = get_graph_name(nl, op)
        else:
            assert(graph_name == get_graph_name(nl, op))
    return graph_name

def get_graph_input_queues(nl, graph_name):
    queues = []
    for op_name in get_op_names(nl, graph_name):
        queues.extend(get_input_queues_for_op(nl, op_name))

    return queues

def get_input_operations_for_op(nl, op):
    ops = []
    for input in get_op_inputs(nl, op):
        if input in get_graph_from_op(nl, op):
            ops.append(input)
    return ops

def get_input_queues_for_op(nl, op):
    queues = []
    op_inputs = get_op_inputs(nl, op)
    for queue in get_queue_names(nl):
        if queue in op_inputs:
            queues.append(queue)
    return queues

def remove_queue(nl,graph_name, queue):
    del_queue(nl, queue)
    remove_input_queues_from_programs(nl, graph_name, [queue])
    pass

def remove_op(nl, operation_name):
    graph_name = get_graph_name(nl, operation_name)
    # first
    for input_operation in get_input_operations_for_op(nl,operation_name):
        fan_out_ops = get_fanout_ops(nl, graph_name, input_operation)
        if operation_name not in fan_out_ops:
            raise Exception(f"Op that is removing {operation_name}")
        fan_out_queues = get_fanout_queues(nl, input_operation)
        if len(fan_out_ops) == 1 and len(fan_out_queues) == 0: # input is dependent only on this op
            # we can remove child op safely
            remove_op(nl, input_operation)

    for input_queue in get_input_queues_for_op(nl, operation_name):
        fan_out_ops = get_fanout_ops(nl, graph_name, input_queue)
        assert(operation_name in fan_out_ops)
        if len(fan_out_ops) == 1: # only one op depends on this queue
            remove_queue(nl, graph_name, input_queue)

    del_op(nl, operation_name)

def add_input_queues_to_programs(nl, graph_name, input_queues):
    for program_dict in nl["programs"]:
        for program in program_dict:
            for program_instruction in program_dict[program]:
                if isinstance( program_instruction, dict):
                    if "execute" in program_instruction and program_instruction["execute"]["graph_name"] == graph_name:
                        queue_settings_dict = program_instruction["execute"]["queue_settings"]

                        # copy input queues from existing netlist
                        for input_queue in input_queues:
                            if input_queue not in queue_settings_dict:
                                queue_settings_dict[input_queue] = queue_settings_dict[list(queue_settings_dict.keys())[0]]

def remove_input_queues_from_programs(nl, graph_name, input_queues):
    for program_dict in nl["programs"]:
        for program in program_dict:
            for program_instruction in program_dict[program]:
                if isinstance( program_instruction, dict):
                    if "execute" in program_instruction and program_instruction["execute"]["graph_name"] == graph_name:
                        queue_settings_dict = program_instruction["execute"]["queue_settings"]

                        # copy input queues from existing netlist
                        for input_queue in input_queues:
                            if input_queue in queue_settings_dict:
                                del queue_settings_dict[input_queue]

def remove_graph(nl, graph_name):
    del_graph(nl, graph_name)

    programs = {}
    for program_dict in nl["programs"]:
        for program in program_dict:
            new_program = []
            keep_program = False
            for program_instruction in program_dict[program]:
                append = True
                if isinstance( program_instruction, dict):
                    if "execute" in program_instruction:
                        if program_instruction["execute"]["graph_name"] != graph_name:
                            keep_program = True
                        else:
                            append = False
                if append:
                    new_program.append(program_instruction)
            if keep_program:
                programs[program] = new_program

    nl["programs"] = []
    for program in programs:
        nl["programs"].append({program:programs[program]})

def add_queues(nl, queues):
    trace(f"adding queues: {list(queues.keys())}")
    nl["queues"].update(queues)

def add_input_queues(nl, graph_name, input_queues):
    # update netlist queues
    add_queues(nl, input_queues)
    # update each program with specific name
    add_input_queues_to_programs(nl, graph_name, input_queues)

# return fan in list of inputs and operations for provided operation
def get_fan_in_for_op(netlist_yaml, operation_name):
    graph = get_graph_from_op(netlist_yaml, operation_name)
    in_queues = []
    in_ops = []
    for input in graph[operation_name]["inputs"]:
        if input in graph:
            ins, ops = get_fan_in_for_op(netlist_yaml, input)
            in_ops.append(input)
            in_ops.extend(ops)
            in_queues.extend(ins)
        else:
            in_queues.append(input)
    return in_queues, in_ops

def raise_interdependency_error(nl, operations):
    for op1 in operations:
        queues, ops = get_fan_in_for_op(nl, op1)
        for op2 in operations:
            if op2 in ops:
                raise Exception(f"Operation {op2} is on input path of operation {op1}")

# returns list of fanout operations for specific input
def get_fanout_ops(nl, graph_name, input):
    result = []
    for op_name in get_op_names(nl, graph_name):
        if input in get_op_inputs(nl, op_name):
            result.append(op_name)
    return result

# returns list of fanout queues for specific operation
def get_fanout_queues(nl, input):
    result = []
    for q_name in get_queue_names(nl):
        if input == get_queue_input(nl, q_name):
            result.append[q_name]
    return result

def remove_ticks(d):
    r = d.__str__().replace('\'', '')
    r = r.replace(' None,', ' ,')
    return r.replace(' None}', ' }')

def is_new_section(line):
    return len(line) > 1 and line[0] != " "

def get_section(line):
    if (line.startswith(SECTION_QUEUES)):
        return SECTION_QUEUES

    if (line.startswith(SECTION_GRAPHS)):
        return SECTION_GRAPHS

    if (line.startswith(SECTION_PROGRAMS)):
        return SECTION_PROGRAMS

    return ""

def render_queue_section(nl, queues):
    result = []
    result.append(SECTION_QUEUES)
    for q_name in queues:
        queue = get_queue(nl, q_name)
        memory =queue[queue['loc']]
        for cnt in range(0, len(memory)):
            if isinstance(memory[cnt], list):
                memory[cnt][1] = f"0x{memory[cnt][1]:02x}"
            else:
                memory[cnt] = f"0x{memory[cnt]:02x}"
        result.append(f"  {q_name}: {remove_ticks(queue)}")
    return result

def render_graph_section(nl, graph_name, operations):
    result = []
    result.append(SECTION_GRAPHS)
    result.append("  "+graph_name+":")
    graph = get_graph(nl, graph_name)

    for item in graph:
        if not isinstance(graph[item], dict):
            result.append(f"    {item}: {graph[item]}")

    for op in operations:
        result.append(f"    {op}: {remove_ticks(graph[op])}")
    return result

def create_new_programs(nl, graph_name, input_queues):
    programs = []
    # 1) extract needed data from program
    for program_dict in nl["programs"]:
        temp_program_dict = {}
        # remove graphs and operations
        for program in program_dict:
            temp_program_list = []
            program_executable = False
            instruction_list = program_dict[program]
            for program_instruction in instruction_list:
                if isinstance( program_instruction, dict):
                    if "execute" in program_instruction:
                        if (program_instruction["execute"]["graph_name"] == graph_name):
                            program_executable = True
                            execute_program = {}
                            execute_program["graph_name"] = graph_name
                            execute_program["queue_settings"] = {}
                            queue_settings_dict = program_instruction["execute"]["queue_settings"]

                            # copy input queues from existing netlist
                            for queue_name in queue_settings_dict:
                                if queue_name in input_queues:
                                    execute_program["queue_settings"][queue_name] = queue_settings_dict[queue_name]

                            exe_cmd = {}
                            exe_cmd["execute"] = execute_program
                            temp_program_list.append(exe_cmd)
                    else:
                        temp_program_list.append(program_instruction)
                else:
                    temp_program_list.append(program_instruction)
            if program_executable:
                temp_program_dict[program] = temp_program_list
        if temp_program_dict:
            programs.append(temp_program_dict)
    return programs

def render_program_section(programs):
    result = []
    result.append(SECTION_PROGRAMS)
    loop_space = ""
    for program in programs:
        for program_name in program:
            result.append(f"  - {program_name}:")
            for command in program[program_name]:
                if isinstance(command, dict):
                    for element in command:
                        if element == "execute":
                            result.append(f"    - {loop_space}{element}: "+"{graph_name: "+command[element]["graph_name"]+", queue_settings: {")
                            s = ",\n".join([ f"               {key}: {remove_ticks(val)}" for (key,val) in command[element]["queue_settings"].items()])
                            s = s + "} }"
                            result.append(s)
                        else:
                            result.append(f"    - {loop_space}{element}: {remove_ticks(command[element])}")
                        if element == "loop":
                            loop_space = "  "
                else:
                    assert(command=="endloop")
                    loop_space=""
                    result.append(f"    - {command}")
    return result

def create_new_netlist(nl, netlist_filename, graph_name, queue_names, operation_names):
    result = []
    with open(netlist_filename) as fr:
        current_section = ""
        while(True):
            line = fr.readline()
            if line == "":
                break

            if is_new_section(line):
                current_section = get_section(line)
                if current_section == SECTION_QUEUES:
                    result.extend(render_queue_section(nl, queue_names))
                    current_section = "skip"

                if current_section == SECTION_GRAPHS:
                    result.extend(render_graph_section(nl, graph_name, operation_names))
                    current_section = "skip"

                if current_section == SECTION_PROGRAMS:
                    programs = create_new_programs(nl, graph_name, queue_names)
                    result.extend(render_program_section(programs))
                    current_section = "skip"

            if (current_section=="skip"):
                continue

            result.append(line.rstrip())

    return result

def get_tapout_queue(netlist, operation_name):
    global tapout
    g, o = tapout_sweep.NetlistReader(netlist).get_graph_op(operation_name)
    if not tapout:
        tapout = tapout_sweep.NetlistTapOut(netlist)
    return tapout.generate_tapout_queue_as_string(g, o)

def get_tapout_queues(netlist, operations):
    global tapout
    nr = tapout_sweep.NetlistReader(netlist)
    if not tapout:
        tapout = tapout_sweep.NetlistTapOut(netlist)

    result = {}
    for op_name in operations:
        g, o = nr.get_graph_op(op_name)
        result.update(tapout.generate_tapout_queue_as_dict(g, o))
    return result

def get_graph_name_to_slice(nl, in_ops, in_op_inputs, out_ops):
    l = [*in_ops, *in_op_inputs, *out_ops]
    graph_name = get_graph_name_from_list(nl, l)
    if (graph_name == "" and len(l)>0):
        raise Exception(f"Operations: {l}, not found in netlist")

    return graph_name

def netlist_slice(netlist_filename, in_ops, in_op_inputs, out_ops):
    try:
        nl = yaml.safe_load(open(netlist_filename))

        # 1. Get graph name. Currently only one graph is suported.
        graph_name = get_graph_name_to_slice(nl, in_ops, in_op_inputs, out_ops)

        # Add inputs of in_op_inputs to in_ops with in_op_inputs
        for in_op in in_op_inputs:
            for input in get_input_operations_for_op(nl, in_op):
                if input not in in_ops:
                    in_ops.append(input)

        # All input queues for graph will be HOST
        for queue in get_graph_input_queues(nl, graph_name):
            set_queue_input(nl, queue, "HOST")

        # 2. Remove graphs/programs that are not needed
        for gr_name in get_graph_names(nl):
            if gr_name != graph_name:
                remove_graph(nl, gr_name)

        # 3. Remove unused queues
        for q_name in get_queue_names(nl):
            if not get_fanout_ops(nl, graph_name, q_name) and get_queue_input(nl, q_name) not in get_graph(nl, graph_name):
                del_queue(nl, q_name)

        # 4. Add new input queues
        #    Modify netlist queue section
        in_queues = get_tapout_queues(netlist_filename, in_ops)
        for q_name in in_queues:
            in_queues[q_name]["input"] = "HOST"
        add_input_queues(nl, graph_name, in_queues)

        # 5. Modify netlist graph section
        #    in_ops are becoming new inputs.
        #    Removes inputs of operations with new input queues
        for in_op in in_ops:
            fan_out_ops = get_fanout_ops(nl, graph_name, in_op)
            fan_out_queues = get_fanout_queues(nl, in_op)
            if len(fan_out_ops) == 0 and len(fan_out_queues) > 0:
                raise Exception(f"in_op operation {in_op} is input only for output {get_fanout_queues(nl, in_op)} queues")

            for fan_out_op in fan_out_ops:
                modified_inputs = ["DBG_" + input if input == in_op else input for input in get_op_inputs(nl, fan_out_op)]
                set_op_inputs(nl, fan_out_op, modified_inputs)

        # 6. After replacing input operations with input queues
        #    remove input operations and all operations and queues 
        #    which are not needed
        for op in in_ops:
            remove_op(nl, op)

        # changing ublock order for output operations
        for op_name in out_ops:
            op = get_op(nl, op_name)
            if "ublock_order" in op:
                print(f"WARNING: Changing ublock_order for operation {op_name} to r")
                op["ublock_order"] = "r"

        # 7. Add tapout_queues to out operations
        out_queues = get_tapout_queues(netlist_filename, out_ops)
        add_queues(nl, out_queues)

        # 8. Find list of needed queues and operations in netlist
        #   a) Find all needed input queues and operations in netlist to feed right_operations
        #   b) Update queues with new output queue list which are tapout queue list from
        queues = []
        ops = []
        if out_ops:
            for out_op in out_ops:
                queues1, ops1 = get_fan_in_for_op(nl, out_op)
                for q in queues1:
                    if q not in queues:
                        queues.append(q)
                for o in ops1:
                    if o not in ops:
                        ops.append(o)

            queues.extend(out_queues)
            ops.extend(out_ops)
        else:
            # just add all operations
            queues = get_queue_names(nl)
            ops = get_op_names(nl, graph_name)

        # 9. Render netlist by only rendering provided queues and operations
        return create_new_netlist(nl, netlist_filename, graph_name, queues, ops)

    except Exception as e:
        traceback.print_exc()

def main():
    global trace_enabled
    parser = argparse.ArgumentParser(description=__doc__ )
    parser.add_argument('--netlist', type=str, required=True, help='Netlist filename')
    parser.add_argument('--in_ops', type=str, required=False, help='List of operations that will be replaced with input queues')
    parser.add_argument('--in_op_inputs', type=str, required=False, help='List of operations which inputs will be replaced with input queues')
    parser.add_argument('--out_ops', type=str, required=False, help='List of operations whose outputs will be replaced with ouput queues')
    parser.add_argument('--out_file', type=str, required=False, help='Output filename')
    parser.add_argument('--verbose', action='store_true', default=False, help=f'Prints additional information.')
    args = parser.parse_args()

    if not os.path.exists(args.netlist):
        print(f"Netlist filename: {args.netlist}, does not exist")
        exit(1)

    if not args.in_ops and not args.out_ops and not args.in_op_inputs:
        print(f"At least one in_ops, in_op_inputs or out_ops should be supplied")
        exit(1)

    trace_enabled = args.verbose

    sliced_netlist = netlist_slice(
        args.netlist,
        args.in_ops.split() if args.in_ops else [],
        args.in_op_inputs.split() if args.in_op_inputs else [],
        args.out_ops.split() if args.out_ops else [])

    if args.out_file:
        with open(args.out_file, "w") as f:
            f.write("\n".join(sliced_netlist))
    else:
        print("\n".join(sliced_netlist))

if __name__ == "__main__":
    main()