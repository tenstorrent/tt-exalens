#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
import sys, os, yaml, zipfile
from tabulate import tabulate
from ordered_set import OrderedSet
import traceback

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
CLR_ORANGE = '\033[38:2:205:106:0m'
CLR_END = '\033[0m'

CLR_ERR = CLR_RED
CLR_WARN = CLR_ORANGE
CLR_INFO = CLR_BLUE

CLR_PROMPT = "<style color='green'>"
CLR_PROMPT_END = "</style>"

# Colorized messages
def VERBOSE(s):
    global args # Expecting this to be set on the module externally
    if "verbose" in args and args.verbose:
        print (f"{CLR_END}{s}{CLR_END}")
def INFO(s):
    print (f"{CLR_INFO}{s}{CLR_END}")
def WARN(s):
    print (f"{CLR_WARN}{s}{CLR_END}")
def ERROR(s):
    print (f"{CLR_ERR}{s}{CLR_END}")
def FATAL(s):
    ERROR (s)
    sys.exit (1)

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

# Stores all data loaded from a yaml file
# Includes a cache in case a file is loaded multiple files
class YamlFile:
    # Cache
    file_cache = {}

    def __init__ (self, filepath):
        self.filepath = filepath

    def load (self):
        if self.filepath in YamlFile.file_cache:
            self.root = YamlFile.file_cache[self.filepath]
        else:
            INFO (f"Loading '{self.filepath}'")
            # Since some files (Pipegen.yaml) contain multiple documents (separated by ---): We merge them all into one map.
            self.root = dict()

            for i in yaml.load_all(open(self.filepath), Loader=yaml.CSafeLoader):
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
    return OrderedSet(*args, **kwargs)