User Guide
==========

PyBuda Introduction
-------------------

A typical PyBuda flow has 4 steps:

#. Define devices to run workload on
#. Place modules from the workload onto devices
#. Run workload
#. Retrieve results

PyBuda API and workflow is flexible enough that some of these steps can be merged, reordered, or skipped altogether, however it helps to work through this basic workflow to understand PyBuda concepts.

Devices
*******

PyBuda makes it easy to distribute a workload onto a heterogenous set of devices available to you. This can be one or more 
Tenstorrent devices, CPUs, or GPUs. Each device that will be used to run your workflow needs to be declared by creating the appropriate
device type and giving it a unique name:

.. code-block:: python

   tt0 = TTDevice("tt0")
   cpu0 = CPUDevice("cpu0")
