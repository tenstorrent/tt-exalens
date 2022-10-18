For developers
==============

Smoke test
----------

Run a very basic test of debuda with: ``dbd/test/test-debuda-py.sh``. This test will run a simple
netlist and start debuda.py.

Offline tests
-------------

Offline tests are stored in ``dbd/test/exported-runs``. They are in binary form. Run the following command
to extract them: ``dbd/test/exported-runs/unpack.sh``. 

After unzipping, you should go into the test directory
and start debuda.py from there. E.g.:
``cd test/exported-runs/simple-matmul-no-hangs && ../../../debuda.py --server-cache on``

Low Level Debug
---------------

Low level messages (debug and trace) are printed in debuda-server source code with the following calls:

.. code-block::

    log_trace(tt::LogDebuda, ...)
    log_debug(tt::LogDebuda, ...)

Make sure all relevant source code is compiled with ``CONFIG=Debug`` in the environment to enable
trace and debug messages.
When running debuda-server, add ``LOGGER_LEVEL=Trace`` or ``LOGGER_LEVEL=Debug`` to enable the messasges.


Visual Studio Code
------------------

Debuda comes with specific debug targets for VS Code. These are configured in ``dbd/launch.json``. You
need add the ``dbd`` folder to workspace to make them available.



Classes
-------

Result of ``autoclass:: tt_graph.Graph``

.. autoclass:: tt_graph.Graph
    :members:

Result of ``automodule:: debuda_commands.testtest``

.. automodule:: debuda_commands.testtest
    :members:
