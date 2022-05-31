#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
import sys, os
from tabulate import tabulate

# Get path of this script. 'frozen' means packaged with pyinstaller.
def application_path ():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path

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
        table = [ [k, dct[k]] for k in dct ]
    else:
        table = [ [ "", "" ] ]
    return table

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
