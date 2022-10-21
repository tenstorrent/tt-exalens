"""The result of the *export* command is similar to a 'core dump' in a conventional program.
It allows one to run the debugger (debuda.py) offline.

The exported file is a zip file containing all relevant yaml files, server cache and command history.

**Limitation**: Only the data read from the chip will be saved in the cache. As a result of this limitation,
one needs to run a set of commands online before being able to rerun them offline.

"""
import tt_util as util
command_metadata = {
    "short" : "xp",
    "type" : "dev", # Not yet production ready. TODO: make sure all the files are properly exported
    "expected_argument_count" : [ 0, 1 ],
    "arguments" : "filename",
    "description" : f"Exports a zip package for offline work. The filename argument is optional. It defaults to '{ util.DEFAULT_EXPORT_FILENAME }'"
}

import tt_device

def run(args, context, ui_state = None):
    navigation_suggestions = []

    zip_file_name = args[1] if len(args) > 1 else util.DEFAULT_EXPORT_FILENAME

    # 1. Add all Yaml files
    filelist = [ f for f in util.YamlFile.file_cache ]
    util.VERBOSE (f"Export filelist: {filelist}")

    # 2. See if server cache is made
    if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled:
        tt_device.DEBUDA_SERVER_CACHED_IFC.save()
        filelist.append (tt_device.DEBUDA_SERVER_CACHED_IFC.filepath)
    else:
        util.WARN ("Warning: server cache is missing and will not be exported (see '--server-cache')")

    # 3. Save command history
    COMMAND_HISTORY_FILENAME="debuda-command-history.yaml"
    util.write_to_yaml_file (context.prompt_session.history.get_strings(), COMMAND_HISTORY_FILENAME)
    filelist.append (COMMAND_HISTORY_FILENAME)

    odir = context.args.output_dir
    if util.export_to_zip (filelist, out_file=zip_file_name, prefix_to_remove=odir):
        print (f"Exported '{zip_file_name}'. Import with:\n{util.CLR_GREEN}unzip {zip_file_name} -d dbd-export-{odir} && cd dbd-export-{odir} && ../{context.debuda_path} . {'--server-cache on' if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled else ''}{util.CLR_END}")

    return navigation_suggestions
