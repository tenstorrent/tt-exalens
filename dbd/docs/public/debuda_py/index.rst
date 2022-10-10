Debuda.py
=========

Debuda.py is a silicon debugger. It reads the output of Buda backend, and the state of silicon
to show and analyze the current state of a Buda run.

.. image:: ../../images/debuda.png

It can operate in three distinct modes:

- Buda-server: while Buda is still running
- Standalone-server: useful when Buda crashes, but chip is available
- Offline: with no hardware connected. Requires prior caching of chip communication.

Command levels
--------------

- No run required: examine nestlist, connectivity, placement geography
- Runtime info present: probe chip state, analyze hangs, etc.

Invocation (CLI arguments)
--------------------------

.. argparse::
   :module: debuda
   :func: get_parser
   :prog: debuda

Commands
--------

Housekeeping
************

(x, export, reload)

.. warning::
  not finished

Low level device access
***********************

(pci-read, ...)

.. warning::
  not finished

High level access and analysis
******************************

.. warning::
  not finished

(queue, ha, ...)



.. automodule:: debuda_commands.testtest
    :members: