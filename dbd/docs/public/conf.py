# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'Debuda'
copyright = '2022, Tenstorrent'
author = 'Tenstorrent'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinxarg.ext', 'sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.autosummary', 'sphinx.ext.autosectionlabel']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_logo = 'images/tt_logo.svg'
html_favicon = 'images/cropped-favicon-32x32.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_member_order = 'bysource'
add_module_names = False


import fnmatch, importlib
def generate_commands_rst ():
    cmd_files = []
    dbd_commands_dir = os.path.abspath(os.curdir) + '/dbd/debuda_commands'
    for root, dirnames, filenames in os.walk(dbd_commands_dir):
        for filename in fnmatch.filter(filenames, '*.py'):
            cmd_files.append(os.path.join(root, filename))
    cmd_files.sort()

    sys.path.append(dbd_commands_dir)

    for cmdfile in cmd_files:
        module_path = os.path.splitext(os.path.basename(cmdfile))[0]
        try:
            cmd_module = importlib.import_module (module_path)
        except Exception as e:
            print (f"Error in module {module_path}: {e}")
            continue
        command_metadata = cmd_module.command_metadata
        command_metadata["module"] = cmd_module
        print (f"{cmdfile}: {cmd_module.__doc__}")

def setup(app):
    app.add_css_file('tt_theme.css')
    print ("-------------------------")
    generate_commands_rst ()