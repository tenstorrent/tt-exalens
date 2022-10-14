#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
import sys, os, yaml, zipfile
from tabulate import tabulate
from sortedcontainers import SortedSet
import traceback, socket

# Pretty print exceptions (traceback)
def notify_exception(exc_type, exc_value, tb):
    rows=[]
    ss_list = traceback.extract_tb(tb)
    cwd_path = os.path.abspath (os.getcwd()) + os.sep
    indent = 0
    fn = "-"
    line_number = "-"
    for ss in ss_list:
        file_name, line_number, func_name, text = ss
        abs_filename = os.path.abspath(file_name)
        fn = os.path.relpath (abs_filename)
        row = [ f"{fn}:{line_number}", func_name, f"{CLR_BLUE}{'  '*indent}{text}{CLR_END}"]
        rows.append (row)
        if indent < 10:
            indent+=1
    rows.append ([ f"{CLR_RED}{fn}:{line_number}{CLR_END}", f"{CLR_RED}{func_name}{CLR_END}", f"{CLR_RED}{exc_type.__name__}: {exc_value}{CLR_END}"])
    print (tabulate(rows))

# Replace the exception hook to print a nicer output
sys.excepthook = notify_exception

# Get path of this script. 'frozen' means packaged with pyinstaller.
def application_path ():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path

def to_hex_if_possible (val):
    if type(val) == int and (val > 9 or val < 0):
        return f" (0x{val:x})"
    else:
        return ''

def with_hex_if_possible (val):
    return f"{val}{to_hex_if_possible(val)}"

# Colors
CLR_RED = '\033[31m'
CLR_GREEN = '\033[32m'
CLR_BLUE = '\033[34m'
CLR_GREY = '\033[37m'
CLR_ORANGE = '\033[38:2:205:106:0m'

CLR_END = '\033[0m'

CLR_ERR = CLR_RED
CLR_WARN = CLR_ORANGE
CLR_INFO = CLR_BLUE

CLR_PROMPT = "<style color='green'>"
CLR_PROMPT_END = "</style>"

# We create a fatal exception that must terminate the program
# All other exceptions might get caught and the program might continue
class TTFatalException (Exception):
    pass

# Colorized messages
def NULL_PRINT(s):
    pass
def VERBOSE(s):
    print (f"{CLR_END}{s}{CLR_END}")
def INFO(s):
    print (f"{CLR_INFO}{s}{CLR_END}")
def WARN(s):
    print (f"{CLR_WARN}{s}{CLR_END}")
def ERROR(s):
    print (f"{CLR_ERR}{s}{CLR_END}")
def FATAL(s):
    ERROR (s)
    raise TTFatalException(s)

# Given a list l of possibly shuffled integers from 0 to len(l), the function returns reverse mapping
def reverse_mapping_list(l):
    ret = [0] * len(l)
    for idx, val in enumerate(l):
        ret[val] = idx
    return ret

# Converts a shallow dict to a table. A table is an array that can be consumed by tabulate.py
def dict_to_table (dct):
    if dct:
        table = [ [k, with_hex_if_possible (dct[k])] for k in dct ]
    else:
        table = [ [ "", "" ] ]
    return table

# Print noc0 coordinates as x-y, and RC coords as [r,c]
def noc_loc_str (noc_loc):
    return f"{noc_loc[0]}-{noc_loc[1]}"
def rc_loc_str (rc_loc):
    return f"[{rc_loc[0]},{rc_loc[1]}]"

# Given two tables 'a' and 'b' merge them into a wider table
def merge_tables_side_by_side (a, b):
    width_a = len(a[0])
    width_b = len(b[0])
    t = [ ]
    for i in range (max (len(a), len(b))):
        row = [ None ] * (width_a + width_b)

        for j in range (width_a):
            row [j] = "" if i >= len(a) else a[i][j]

        for j in range (width_b):
            row [j + width_a] = "" if i >= len(b) else b[i][j]

        t.append (row)
    return t

# Given an array of dicts, and their titles. Print a flattened version of all the dicts as a big table.
def print_columnar_dicts (dict_array, title_array):
    final_table = [ ]
    for idx, dct in enumerate(dict_array):
        assert isinstance(dct, dict)
        current_table = dict_to_table(dct)
        if idx == 0:
            final_table = current_table
        else:
            final_table = merge_tables_side_by_side (final_table, current_table)

    titles = [ ]
    for t in title_array:
        titles += [ t ]
        titles += [ "" ]

    print (tabulate(final_table, headers=titles))

# Container for YAML
class YamlContainer:
    def __init__ (self, yaml_string):
        self.root = dict()
        for i in yaml.load_all(yaml_string, Loader=yaml.CSafeLoader):
            self.root = { **self.root, **i }

# Stores all data loaded from a yaml file
# Includes a cache in case a file is loaded multiple times
class YamlFile:
    # Cache
    file_cache = {}

    def __init__ (self, filepath):
        self.filepath = filepath
        YamlFile.file_cache[self.filepath] = None # Not loaded yet

    def load (self):
        if self.filepath in YamlFile.file_cache and YamlFile.file_cache[self.filepath]:
            self.root = YamlFile.file_cache[self.filepath]
        else:
            INFO (f"Loading '{os.getcwd()}/{self.filepath}'")
            # Since some files (Pipegen.yaml) contain multiple documents (separated by ---): We merge them all into one map.
            # Note: graph_name can apear multiple times, we manually convert it into an array
            self.root = dict()

            for i in yaml.load_all(open(self.filepath), Loader=yaml.CSafeLoader):
                if 'graph_name' in i:
                    if 'graph_names' not in self.root:
                        self.root['graph_names'] = []
                    self.root['graph_names'].append (i['graph_name'])
                else:
                    self.root = { **self.root, **i }
            YamlFile.file_cache[self.filepath] = self.root

    def __str__(self):
        return f"{type(self).__name__}: {self.filepath}"
    def items(self):
        return self.root.items()
    def id(self):
        return self.filepath

    def __getattr__(self, name):
        if name == "root":
            self.load()
        return object.__getattribute__(self, name)

DEFAULT_EXPORT_FILENAME='debuda-export.zip'

# Exports filelist to a zip file
def export_to_zip(filelist, out_file=DEFAULT_EXPORT_FILENAME):
    if out_file is None: out_file=DEFAULT_EXPORT_FILENAME
    if os.path.exists (out_file):
        WARN (f"Warning: cannot export as the output file already exists: {out_file}")
        return False

    zf = zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED)

    for filepath in filelist:
        zf.write(filepath, filepath)

    return True

def write_to_yaml_file (data, filename):
    with open(filename, 'w') as output_yaml_file:
        yaml.dump(data, output_yaml_file)

# Takes in data in row/column format and returns string with aligned columns
# Usage:
# column_format = [
#     { 'key_name' : None,          'title': 'Name',   'formatter': None },
#     { 'key_name' : 'target_device', 'title': 'Device', 'formatter': lambda x: f"{util.CLR_RED}{x}{util.CLR_END}" },
# ]
# table=util.TabulateTable(column_format)
# ... table.add_row (row_key_name, row_data_dict)
# print (table)
class TabulateTable:

    # How to format across columns.
    # if 'key_name' is None, the 'key' argument to add_row is used for that column
    def __init__ (self, column_format, sort_col = None):
        self.headers =[ col["title"] for col in column_format ]
        self.rows = []
        self.column_format = column_format
        self.sort_col = sort_col

    def add_row (self, key, data):
        row = []

        for col_data in self.column_format:
            if col_data["key_name"] is None:
                element_data=key
            else:
                element_data=data[col_data['key_name']]

            if 'formatter' in col_data and col_data['formatter'] is not None:
                element_data = col_data['formatter'] (element_data)
            row.append (element_data)
        self.rows.append (row)

    def __str__ (self):
        if self.sort_col is not None:
            self.rows.sort (key=lambda x: x[self.sort_col])

        return tabulate (self.rows, headers=self.headers)

def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False

def set(*args, **kwargs):
    return SortedSet(*args, **kwargs)

class CELLFMT:
    def passthrough(r,c,i,val):
        return val
    def odd_even(r,c,i,val):
        if r % 2 == 0: return val
        else: return f"{CLR_GREY}{val}{CLR_END}"
    def hex(bytes_per_entry, prefix ="0x", postfix = ""):
        def hex_formatter(r,c,i,val):
            return prefix + "{vrednost:{fmt}}".format (fmt="0" + str(bytes_per_entry*2) + "x", vrednost=val) + postfix
        return hex_formatter
    def composite(fmt_function_array):
        def cell_fmt(r,c,i,val):
            for f in fmt_function_array:
                val = f(r,c,i,val)
            return val
        return cell_fmt
    def dec_and_hex(r,c,i,val):
        return f"{CLR_BLUE}{i:4d}{CLR_END} 0x{i:08x}"

def array_to_str(A,
    num_cols=8, start_row=None, end_row=None,
    condense=False,
    show_row_index=True, show_col_index=True,
    cell_formatter=CELLFMT.passthrough,
    row_index_formatter=CELLFMT.passthrough
    ):
    lena=len(A)
    if lena==0: return
    if not start_row: start_row=0
    if not end_row: end_row=(lena - 1) // num_cols + 1

    skip_border_rows=4 if condense else 0
    skip_rows_rendered=False

    header = list(range(num_cols))
    rows = []
    for r in range(start_row, end_row):
        if skip_border_rows and (r >= skip_border_rows and r < end_row-skip_border_rows):
            if not skip_rows_rendered:
                rows.append (["..."] * num_cols)
                skip_rows_rendered=True
        else:
            row = [] if not show_row_index else [ row_index_formatter(r,r * num_cols,r * num_cols,r) ]
            for c in range(num_cols):
                i = r * num_cols + c
                if i < lena:
                    row.append(cell_formatter(r,c,i,A[i]))
                else:
                    row.append('')

            rows.append(row)
    return tabulate(rows, headers=header if show_col_index else [])

def dump_memory(addr, array, bytes_per_entry, bytes_per_row, in_hex):
    num_cols = bytes_per_row // bytes_per_entry
    if in_hex:
        cell_formatter = CELLFMT.hex(bytes_per_entry, "")
    else:
        cell_formatter = CELLFMT.passthrough
    def fmt_row_index(addr, bytes_per_entry):
        def hex_formatter(r,c,i,val):
            return "0x{val:08x}".format(val = addr+i*bytes_per_entry)+":"
        return hex_formatter
    row_index_formatter = fmt_row_index(addr, bytes_per_entry)
    return array_to_str(array, num_cols, show_col_index=False, cell_formatter=cell_formatter, row_index_formatter=row_index_formatter)

# A helper function to parse print_format
PRINT_FORMATS = {
    "i32"  : {"is_hex": False, "bytes": 4 },
    "i16"  : {"is_hex": False, "bytes": 2 },
    "i8"   : {"is_hex": False, "bytes": 1 },
    "hex32": {"is_hex": True,  "bytes": 4 },
    "hex16": {"is_hex": True,  "bytes": 2 },
    "hex8" : {"is_hex": True,  "bytes": 1 }}

def word_to_byte_array(A):
    byte_array=[]
    for i in A:
        byte_array.append (i & 0xff)
        byte_array.append ((i>>8) & 0xff)
        byte_array.append ((i>>16) & 0xff)
        byte_array.append ((i>>32) & 0xff)
    return byte_array

# Returns True if port available
def is_port_available(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        result = True
    except:
        pass
    sock.close()
    return result
