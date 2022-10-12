"""Documentation for export
"""
import tt_util as util

command_metadata = {
    "short" : "xp",
    "type" : "housekeeping",
    "expected_argument_count" : [ 0, 1 ],
    "arguments" : "filename",
    "description" : f"Exports a zip package for offline work. The optional argument represents the file name. Defaults to '{ util.DEFAULT_EXPORT_FILENAME }'"
}

import tt_device

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    zip_file_name = args[1] if len(args) > 1 else util.DEFAULT_EXPORT_FILENAME

    # 1. Add all Yaml files
    filelist = [ f for f in util.YamlFile.file_cache ]

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

    if util.export_to_zip (filelist, out_file=zip_file_name):
        print (f"{util.CLR_GREEN}Exported '{zip_file_name}'. Import with:\n  unzip {zip_file_name} -d dbd-export\n  cd dbd-export\n  Run debuda.py {'--server-cache on' if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled else ''}{util.CLR_END}")

    return navigation_suggestions
