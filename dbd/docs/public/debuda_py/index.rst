Debuda.py
=========

Introduction
------------

Debuda.py is a silicon debugger. It reads the output of Buda backend, and the state of silicon
to show and analyze the current state of a Buda run.

It can operate in three distinct modes:

- Buda-server: while Buda is still running
- Standalone-server: useful when Buda crashes, but chip is available
- Offline: with no hardware connected. This mode requires prior caching of chip communication.

.. image:: ../../images/debuda.png

Invocation (CLI arguments)
--------------------------

.. argparse::
   :module: debuda
   :func: get_parser
   :prog: debuda

Commands
--------

.. include:: commands.generated-rst