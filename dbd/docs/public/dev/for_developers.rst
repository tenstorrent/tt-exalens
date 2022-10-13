For developers
==============


Low Level Debug
---------------

Low level messages (debug and trace) are printed in debuda-server source code with the following calls:

.. code-block::

    log_trace(tt::LogDebuda, ...)
    log_debug(tt::LogDebuda, ...)

Make sure all relevant source code is compiled with ``CONFIG=Debug`` in the environment to enable
trace and debug messages.
When running debuda-server, add ``LOGGER_LEVEL=Trace`` or ``LOGGER_LEVEL=Debug`` to enable the messasges.


Classes
-------

autoclass:: tt_graph.Graph

.. autoclass:: tt_graph.Graph
    :members:

automodule:: debuda_commands.testtest

.. automodule:: debuda_commands.testtest
    :members:
