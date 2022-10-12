Debuda.py
=========

Introduction
------------

Debuda.py is a silicon debugger. It reads the output of Buda backend, and the state of silicon
to show and analyze the current state of a Buda run.

It can operate in three distinct modes:

1. Built-in Buda server: while Buda is still running

.. image:: ../../images/debuda-buda.png
   :width: 500

2. Standalone server: useful when Buda crashes, but chip is available

.. image:: ../../images/debuda-debuda-server.png
   :width: 500

3. Offline: with no hardware connected. This mode requires prior caching of chip communication.

.. image:: ../../images/debuda-export-db.png
   :width: 600

Invocation (CLI arguments)
--------------------------

.. argparse::
   :module: debuda
   :func: get_parser
   :prog: debuda

Commands
--------

.. include:: commands.generated-rst