#include <string>
#include <map>

const std::string BOOLEAN_FALSE = "FALSE";
const std::string BOOLEAN_TRUE  = "TRUE";

struct ProgramArgument {
    typedef enum {STRING, BOOLEAN, INT} ProgramArgumentType;
    std::string name;
    std::string value;
    std::string description;
    ProgramArgumentType type;
};

typedef std::map<std::string, ProgramArgument> ProgramArguments;

class ProgramArgumentsParser {
    public:
        static void print_usage();
        static ProgramArguments parse_arguments(int argc, char** argv);
        static std::string usage_header;
        static ProgramArguments default_program_arguments;
};