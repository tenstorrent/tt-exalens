#include "program_controller.hpp"
#include "arguments.hpp"

const std::string NETLIST        = "--netlist";
const std::string BIN_INPUT      = "--bin-input";
const std::string SILICON_OUTPUT = "--silicon-output";
const std::string GOLDEN_OUTPUT  = "--golden-output";
const std::string SILICON_DEBUG  = "--silicon-debug";
ProgramArguments ProgramArgumentsParser::default_program_arguments = {
    {NETLIST,        {NETLIST,               "", "Path to netlist file",                                               ProgramArgument::STRING }},
    {BIN_INPUT,      {BIN_INPUT,             "", "Path to input binary files, and generated input files",              ProgramArgument::STRING }},
    {SILICON_OUTPUT, {SILICON_OUTPUT,        "", "Netlist will run on silicon and data will be stored on this path.",  ProgramArgument::STRING }},
    {GOLDEN_OUTPUT,  {GOLDEN_OUTPUT,         "", "Netlist will run on golden and data will be stored on this path.",   ProgramArgument::STRING }},
    {SILICON_DEBUG,  {SILICON_DEBUG,         "", "Backend will not close immediately and wait for key pressed.",       ProgramArgument::BOOLEAN }},

};

std::string ProgramArgumentsParser::usage_header = 
"Golden Run:  ./build/test/dbd/tools/run --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --bin-input t_bin/in --golden-output t_bin/out_g\n"
"Silicon Run: ./build/test/dbd/tools/run --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --bin-input t_bin/in --silicon-output t_bin/out\n"
"Debug  Run:  ./build/test/dbd/tools/run --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --bin-input t_bin/in --silicon-output t_bin/out --silicon-debug\n"
"Diff:        ./build/test/dbd/tools/run --netlist verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml --silicon-output t_bin/out --golden-output t_bin/out_g\n";



int main(int argc, char** argv) {

    ProgramArguments arguments = ProgramArgumentsParser::parse_arguments(argc, argv);
    ProgramConfig config(arguments[NETLIST].value);

    if (!arguments[BIN_INPUT].value.empty()) {
        if (!arguments[GOLDEN_OUTPUT].value.empty()) {
            CommonProgramController golden(
                config,
                arguments[BIN_INPUT].value,
                arguments[GOLDEN_OUTPUT].value,
                false);
            golden.run();
        }

        if (!arguments[SILICON_OUTPUT].value.empty()) {
            if (arguments[SILICON_DEBUG].value.empty()) {
                CommonProgramController silicon(
                    config,
                    arguments[BIN_INPUT].value,
                    arguments[SILICON_OUTPUT].value,
                    true);
                silicon.run();
            } else {
                std::shared_ptr<IBackend> backend = BackendFactory::create_golden_debug(config.get_netlist_path());
                CommonProgramController silicon(
                    config,
                    arguments[BIN_INPUT].value,
                    arguments[SILICON_OUTPUT].value,
                    backend);
                silicon.run();
                if (arguments[SILICON_DEBUG].value == BOOLEAN_TRUE) {
                    cout << "Please press any key ...";
                    std::cin.ignore();
                }
            }
        }
    }

    if (!arguments[SILICON_OUTPUT].value.empty() && !arguments[GOLDEN_OUTPUT].value.empty()){
        DiffChecker diff(config, arguments[SILICON_OUTPUT].value, arguments[GOLDEN_OUTPUT].value);
        diff.run_check();
        return diff.is_success() ? 0 : 1;
    }

    return 0;
}