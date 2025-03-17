# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import sys, os, traceback
from tabulate import tabulate
from ttexalens import Verbosity
from ttexalens.utils.exceptions import TTFatalException, TTException
import functools, types

# Colors
CLR_RED    = "\033[31m"
CLR_GREEN  = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BLUE   = "\033[34m"
CLR_VIOLET = "\033[35m"
CLR_TEAL   = "\033[36m"
CLR_GREY   = "\033[37m"
CLR_ORANGE = "\033[38:2:205:106:0m"
CLR_WHITE  = "\033[38:2:255:255:255m"
CLR_END    = "\033[0m"

CLR_ERR = CLR_RED
CLR_WARN = CLR_ORANGE
CLR_INFO = CLR_BLUE
CLR_VERBOSE = CLR_GREY
CLR_DEBUG = CLR_GREEN

CLR_PROMPT = "<style color='green'>"
CLR_PROMPT_END = "</style>"
CLR_PROMPT_BAD_VALUE = "<style color='red'>"
CLR_PROMPT_BAD_VALUE_END = "</style>"

# Pretty print exceptions (traceback)
def notify_exception(exc_type, exc_value, tb):
    rows = []
    ss_list = traceback.extract_tb(tb)
    indent = 0
    fn = "-"
    line_number = "-"
    for ss in ss_list:
        file_name, line_number, func_name, text = ss
        abs_filename = os.path.abspath(file_name)

        # Exceptions thrown from importlib might not have a file in all stack frames
        if os.path.exists(abs_filename):
            fn = os.path.relpath(abs_filename)
            row = [
                f"{fn}:{line_number}",
                func_name,
                f"{CLR_BLUE}{'  '*indent}{text}{CLR_END}",
            ]
            rows.append(row)
            if indent < 10:
                indent += 1

    rows.append(
        [
            f"{CLR_RED}{fn}:{line_number}{CLR_END}",
            f"{CLR_RED}{func_name}{CLR_END}",
            f"{CLR_RED}{exc_type.__name__}: {exc_value}{CLR_END}",
        ]
    )

    # Exceptions thrown from importlib set these
    if hasattr(exc_value, "filename") and hasattr(exc_value, "lineno"):
        rows.append(
            [
                f"{CLR_RED}{os.path.relpath(exc_value.filename)}:{exc_value.lineno}{CLR_END}",
                f"{CLR_RED}{func_name}{CLR_END}",
                f"{CLR_RED}{exc_type.__name__}: {exc_value.text}{CLR_END}",
            ]
        )

    print(tabulate(rows, disable_numparse=True))


# Basic logging functions
# Colorized messages
def NULL_PRINT(s):
    pass


def PRINT(s, **kwargs):
    print(f"{CLR_END}{s}", **kwargs)


def FATAL(s, **kwargs):
    ERROR(s, **kwargs)
    raise TTFatalException(s)


def ERROR(s, **kwargs):
    if Verbosity.supports(Verbosity.ERROR):
        print(f"{CLR_ERR}{s}{CLR_END}", **kwargs)


def WARN(s, **kwargs):
    if Verbosity.supports(Verbosity.WARN):
        print(f"{CLR_WARN}{s}{CLR_END}", **kwargs)


def DEBUG(s, **kwargs):
    if Verbosity.supports(Verbosity.DEBUG):
        print(f"{CLR_DEBUG}{s}{CLR_END}", **kwargs)


def INFO(s, **kwargs):
    if Verbosity.supports(Verbosity.INFO):
        print(f"{CLR_INFO}{s}{CLR_END}", **kwargs)


def VERBOSE(s, **kwargs):
    if Verbosity.supports(Verbosity.VERBOSE):
        print(f"{CLR_VERBOSE}{s}{CLR_END}", **kwargs)


# Set our custom exception hook
sys.excepthook = notify_exception

# Global variable to keep track of the nesting level of the trace. Used to indent the printout.
TRACE_NESTING_LEVEL = 2
TRACER_FUNCTION = INFO  # By default we show the trace with INFO level


def trace(func):
    """Decorator that prints the comment of the function when it's called.
    The function must have a docstring to be traced."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global TRACE_NESTING_LEVEL
        doc = func.__doc__

        # Collecting arguments and their values for the printout
        args_list = [repr(a) for a in args]
        args_list.extend([f"{k}={v!r}" for k, v in kwargs.items()])
        arguments = ", ".join(args_list)

        # Print with indentation
        if doc:
            TRACER_FUNCTION(f"{' ' * TRACE_NESTING_LEVEL}{func.__name__}({arguments}): {doc.strip().splitlines()[0]}")
            # Increase nesting level for nested calls
            TRACE_NESTING_LEVEL += 2

        result = func(*args, **kwargs)

        if doc:
            TRACE_NESTING_LEVEL -= 2

        return result

    return wrapper


def decorate_all_module_functions_for_tracing(mod):
    """Decorates all functions in a given module 'mod' with @trace decorator."""
    global TRACE_NESTING_LEVEL
    TRACE_NESTING_LEVEL = 2
    for name, obj in list(vars(mod).items()):
        if isinstance(obj, types.FunctionType) and obj.__module__ == mod.__name__:
            setattr(mod, name, trace(obj))


def get_indent():
    return " " * TRACE_NESTING_LEVEL


class LOG_INDENT:
    def __enter__(self):
        global TRACE_NESTING_LEVEL
        TRACE_NESTING_LEVEL += 2

    def __exit__(self, exc_type, exc_val, exc_tb):
        global TRACE_NESTING_LEVEL
        TRACE_NESTING_LEVEL -= 2

# Return an ansi color code for a given index. Useful for coloring a list of items.
def clr_by_index(idx):
    return f"\033[{31 + idx % 7}m"


def color_text_by_index(text, color_index):
    return f"{clr_by_index(color_index)}{text}{CLR_END}"