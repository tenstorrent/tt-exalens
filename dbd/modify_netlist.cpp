#include <iostream>
#include <fstream>
#include "netlist/netlist_workload_data.hpp"
#include "model/utils.hpp"
#include "common/size_lib.hpp"

const std::uint32_t c_1GB = 1024 * 1024 * 1024;
const std::uint32_t c_DramChannelSize = c_1GB;
const std::uint32_t c_DramStartAddressForAllocation = 256 * 1024 * 1024;
const std::uint32_t c_DramChannelCount = 8;
const std::uint32_t c_DramBufferHeader = 32;

/////////////////////////////////////////////////////
// Debuda DRAM memory allocation per one channel
class DebudaDramAllocPerChannel {
    public:
        DebudaDramAllocPerChannel(std::uint32_t size) :_size(size) {}
        void insert_allocation(std::uint32_t start_address, std::uint32_t size);
        std::uint32_t allocate(std::uint32_t size);
        void dump();
    private:
        void add(std::uint32_t start_address, std::uint32_t size);
        void insert(size_t index, std::uint32_t start_address, std::uint32_t size);
        std::uint32_t _size;
        std::vector<std::pair<std::uint32_t, std::uint32_t>> _allocations;
};

void DebudaDramAllocPerChannel::add(std::uint32_t start_address, std::uint32_t size) {
    _allocations.push_back(std::make_pair(start_address, size));
}

void DebudaDramAllocPerChannel::insert(size_t index, std::uint32_t start_address, std::uint32_t size) {
    _allocations.insert( _allocations.begin() + index, std::make_pair(start_address, size));
}

void DebudaDramAllocPerChannel::dump() {
    std::cout << "Slot size:" << _size << std::endl;
    for (size_t i = 0; i < _allocations.size(); ++i) {
        std::cout << "Address : " << _allocations[i].first << "\tSize:" << _allocations[i].second << std::endl;
    }
}

void DebudaDramAllocPerChannel::insert_allocation(std::uint32_t start_address, std::uint32_t size) {
    if (size > _size || size == 0 || start_address > _size || start_address > _size - size) {
        throw std::out_of_range("Invalid size");
    }

    if (_allocations.empty()) {
        add(start_address, size);
        return;
    }

    int previous_end_address = 0;
    for (size_t i = 0; i < _allocations.size(); ++i) {
        if (_allocations[i].first <= start_address) {
            previous_end_address = _allocations[i].first + _allocations[i].second;
            if (previous_end_address > start_address) {
                throw std::out_of_range("Overlapping start address");
            }
        } else {
            if (_allocations[i].first - start_address < size) {
                throw std::out_of_range("Overalapping end address");
            }
            insert(i, start_address, size);
            return;
        }
    }

    add(start_address, size);
}

std::uint32_t DebudaDramAllocPerChannel::allocate(std::uint32_t size) {
    if (size > _size || size == 0) {
        throw std::out_of_range("Invalid size");
    }

    int previous_end_address = 0;
    for (size_t i = 0; i < _allocations.size(); ++i) {
        if (_allocations[i].first - previous_end_address > size) {
            insert(i, previous_end_address, size);
            return previous_end_address;
        }
        previous_end_address = _allocations[i].first + _allocations[i].second;
    }

    if (previous_end_address < _size && previous_end_address <= _size - size) {
        add(previous_end_address, size);
        return previous_end_address;
    }

    return 0;
}

//////////////////////////////////////////////////////
// Debuda DRAM memory allocation per group of channels
class DebudaDramAllocation {
    public:
        DebudaDramAllocation(std::uint32_t channel_cnt, std::uint32_t size)
        : _channels(channel_cnt, DebudaDramAllocPerChannel(size)) {

        }

        void insert_allocation(std::uint32_t channel_id, std::uint32_t address, std::uint32_t size) {
            _channels[channel_id].insert_allocation(address, size);
        }

        std::uint32_t allocate(std::uint32_t channel_id, std::uint32_t size) {
            return _channels[channel_id].allocate(size);
        }

        void dump() {
            for (size_t n = 0; n < _channels.size(); ++n) {
                std::cout << "channel_id : " << n << std::endl;
                _channels[n].dump();
            }
        }

        size_t channel_count() const { return _channels.size(); }
    private:
        std::vector<DebudaDramAllocPerChannel> _channels;
};



class DebudaNetlistGenerator {
    public:
        DebudaNetlistGenerator(const string& netlist_path) : _workload_data(netlist_path), _ptr_dram_allocation(nullptr), _entries(0) {
            init();
        }

        ~DebudaNetlistGenerator() {
            delete _ptr_dram_allocation;
        }

        void print_operations(std::ostream& output) {
            std::vector<std::pair<std::string, std::string>> operations = get_operations();
            log_info("Operation count : {}", operations.size());

            for(size_t i = 0; i < operations.size(); ++i) {
                std::string graph_name;
                std::string operation_name;
                std::tie(graph_name, operation_name) = operations[i];

                print_operation_as_queue(output, graph_name, operation_name);
            }
        }

        void print_operation_as_queue(std::ostream& output, const std::string& graph_name, const std::string& operation_name){
            const tt_op_info& op = get_op_info(graph_name, operation_name);

            output << "  DBG_" << op.name << ": ";
            for (std::size_t i = op.name.length(); i < 20 + 1; i++) output << " ";

            output << "{type: queue, ";
            output << "input: " << op.name << ", ";

            // TODO: How to get number of entries?
            output << "entries: " << get_entries()<< ", ";

            // TODO: Check if order is good
            output << "grid_size: [" << op.grid_size_x() << ", " << op.grid_size_y() << "], ";

            output << "t: " << op.t << ", ";

            // TODO: check if order is correct ublock_ct or ublock_rt
            output << "mblock: [" << op.mblock_m <<", " << op.mblock_n << "], ublock: [" << op.ublock_rt << ", " << op.ublock_ct << "], ";

            output << "df: " << DATA_FORMAT_TO_STRING.find(op.output_data_format)->second << ", ";
            output << "target_device: " << get_target_device(graph_name) << ", ";

            // TODO: Check if this is always in DRAM
            output << "loc: " << "dram";

            output << ", dram: [";
            auto allocations = allocate(op);
            bool first = true;
            for (auto alloc : allocations) {
                if (!first) output << ", ";
                else first = false;
                output << "[" << alloc.channel << ", 0x" << std::hex << alloc.address << "]";
            }
            output << "]";
            output << "}" << std::endl;
        }
    private:
        void init() {
            // device architecutre is not supported currently
            _ptr_dram_allocation = new DebudaDramAllocation(c_DramChannelCount, c_DramChannelSize);
            // init addresses that should not be used
            for (size_t channel_id = 0; channel_id < _ptr_dram_allocation->channel_count(); ++ channel_id) {
                _ptr_dram_allocation->insert_allocation(channel_id, 0, c_DramStartAddressForAllocation);
            }

            // init addresses from workload
            for (auto queue : _workload_data.queues) {
                if (queue.second.my_queue_info.loc == QUEUE_LOCATION::DRAM) {
                    for (auto alloc : queue.second.my_queue_info.alloc_info) {
                        _ptr_dram_allocation->insert_allocation(alloc.channel, alloc.address, get_buffer_size_needed_for_queue_in_dram(queue.second.my_queue_info));
                    }
                }

                // update entries to max value
                _entries = (queue.second.my_queue_info.entries > _entries) ? queue.second.my_queue_info.entries : _entries;
            }
        }
    
        /// Function that calculates size of buffer based on tt_queue_info
        std::uint32_t get_buffer_size_needed_for_queue_in_dram(const tt_queue_info& qinfo) {
            return get_entry_size_in_bytes(qinfo, true) * qinfo.entries + c_DramBufferHeader;
        }

        std::uint32_t get_buffer_size_needed_for_op_in_dram(const tt_op_info& opInfo) {
            return tt::size::get_entry_size_in_bytes(
                opInfo.output_data_format,
                true,
                opInfo.ublock_ct,
                opInfo.ublock_rt,
                opInfo.mblock_m,
                opInfo.mblock_n,
                opInfo.t) * get_entries() * 2 + c_DramBufferHeader;
        }

        std::vector<tt_queue_allocation_info> allocate(const tt_op_info& op) {
            uint32_t n = op.grid_size_x() * op.grid_size_y();
            std::vector<tt_queue_allocation_info> allocations;

            uint32_t size = get_buffer_size_needed_for_op_in_dram(op);
            for (int i = 0; i < n; ++i) {
                tt_queue_allocation_info alloc_info;
                for (size_t n = 0; n < _ptr_dram_allocation->channel_count(); ++n) {
                    uint32_t address = _ptr_dram_allocation->allocate(n, size);
                    if (address != 0) {
                        alloc_info.address = address;
                        alloc_info.channel = n;
                        break;
                    }
                }
                if (alloc_info.address == 0) {
                    throw std::out_of_range("Cannot allocate buffer in dram");
                }
                allocations.push_back(alloc_info);
            }
            return allocations;
        }

        std::uint32_t get_target_device(const std::string& graph_name) {
            return _workload_data.graphs[graph_name].my_graph_info.target_device;
        }

        const tt_op_info& get_op_info(const std::string& graph_name, const std::string& op_name) {
            return _workload_data.graphs[graph_name].my_graph_info.op_map[op_name];
        }

        std::vector<std::pair<std::string, std::string>> get_operations() {

            // get graph run order
            std::vector<std::string> graph_run_order;
            for (auto &it : _workload_data.program_order) {
                std::string graph_name;
                for (auto &instructionIt :_workload_data.programs[it].get_program_trace()) {
                    if(instructionIt.opcode == INSTRUCTION_OPCODE::Execute) {
                        graph_name = instructionIt.graph_name;
                        break;
                    }
                }

                if (graph_name.empty()) {
                    throw std::out_of_range(std::string("Program does not have execute section"));
                }

                graph_run_order.push_back(graph_name);
            }

            // Get opreations that are already inputs in output queues
            std::set<std::string> operations_to_skip;
            for (auto q : _workload_data.queues) {
                operations_to_skip.insert(q.second.my_queue_info.input);
            }

            // get opreations in order of execution
            std::vector<std::pair<std::string, std::string>> operations;
            for (auto &graph_it : graph_run_order)
                for (auto &op_it : _workload_data.graphs[graph_it].op_list)
                    if (operations_to_skip.find(op_it->name) == operations_to_skip.end())
                        operations.push_back(std::make_pair(graph_it, op_it->name));

            return operations;
        }

        std::uint32_t get_entries() const {
            return _entries;
        }

        DebudaDramAllocation* _ptr_dram_allocation;
        netlist_workload_data _workload_data;
        std::uint32_t _entries;
};


struct {
    bool generate_netlist;
    std::string netlist_path;
    std::string output_path;
    string graph_name;
} cmd_args;



void parse_args(int argc, char **argv) {
    std::vector<std::string> args(argv, argv + argc);

    bool help = false;

    string help_string;
    help_string += "dbd_modify_netlist --netlist [netlist_path] \n";
    help_string += "--netlist <>                : Path to netlist file\n";
    help_string += "--o <>                      : Path to output file\n";
    help_string += "--g                         : Generate netlist\n";
    help_string += "--help                      : Prints this message\n";

    try {
        std::tie(cmd_args.netlist_path, args) = args::get_command_option_and_remaining_args(args, "--netlist");
        std::tie(cmd_args.output_path, args) = args::get_command_option_and_remaining_args(args, "--o", "");
        std::tie(cmd_args.generate_netlist, args) = args::has_command_option_and_remaining_args(args, "--g");
        std::tie(help, args) = args::has_command_option_and_remaining_args(args, "--help");
        args::validate_remaining_args(args);
    }
    catch (const std::exception& e) {
        log_error("{}", e.what());
        log_error("Usage Help:\n{}", help_string);
        exit(1);
    }

    if (help) {
        log_info("Usage Help:\n{}", help_string);
        exit(0);
    }
}


int main(int argc, char** argv) {

    parse_args(argc, argv);

    DebudaNetlistGenerator netlist_generator(cmd_args.netlist_path);

    if (cmd_args.generate_netlist) {
        std::ofstream out;
        if (!cmd_args.output_path.empty()) {
            out.open(cmd_args.output_path);
        }

        std::ostream* output= cmd_args.output_path.empty() ? &cout : &out;

        std::ifstream in(cmd_args.netlist_path);
        std::string line;

        bool printed = false;

        while (std::getline(in, line)){
            *output << line << std::endl;
            if (!printed && line.substr(0, 7) == "queues:") {
                netlist_generator.print_operations(*output);
                printed = true;
            }
        }
    }
    else {
        netlist_generator.print_operations(*&cout);
    }

    return 0;
}