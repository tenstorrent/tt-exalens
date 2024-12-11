import yaml,os
from ttlens.tt_util import TTException

class LogInfo:
    def __init__(self, address=0, log_name="", size=0, output="int"):
        self.address = address
        self.log_name = log_name
        self.size = size
        self.output = output
    
def parse_log_yaml(log_yaml_file: str) -> list:
    def parse_address(yaml_data: dict, log_name) -> int:
        if log_name not in yaml_data["record_configurations"]:
            raise TTException(f"Address for log {log_name} not found in yaml file")
        
        addr_str = yaml_data["record_configurations"][log_name]["address"]

        if addr_str.find('+') != -1:
            addr_str = addr_str.replace(' ', '').split('+')
            return yaml_data["base_addresses"][addr_str[0]] + int(addr_str[1], 16)
        else:
            return int(addr_str, 16)

    parsed_data = []

    yaml_data = {}
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../", log_yaml_file)
    with open(file_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    # Hardcoding heartbeat address because it's used as timestamp
    parsed_data.append(LogInfo(address=parse_address(yaml_data, "heartbeat"), log_name="heartbeat"))

    for log in yaml_data['logger_configuration']['records']:
        if log == "heartbeat":
            continue
        size=yaml_data['record_configurations'][log]['size']
        output=yaml_data['record_configurations'][log]['output']
        parsed_data.append(LogInfo(address=parse_address(yaml_data, log), log_name=log,size=size,output=output))
    
    return parsed_data
