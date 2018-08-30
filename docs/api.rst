Using the Web Tools as an Operator
----------------------------------

Once you are pointed to a proper URL to access the webtools, you will
come to the home page, with links to different views.
For each of the examples below, I will use the base URL of ``https://localhost:8080/``,
since that is likely the URL you can see if you run the server on your machine.
If you are looking at a production server, the URL will of course be different.

For users familiar with CherryPy, each page is a function of a ``WorkflowTools`` object.
To pass parameters to the function in a browser,
the usual urlencoding of the parameters can be appended to the URL to call each function.
Most users should be able to interact with the website exclusively through links though.
From the URL root index, users will be able to directly access the following:

- :ref:`global-view-ref`
- :ref:`new-user-ref`
- :ref:`reset-pass-ref`
- :ref:`show-logs-ref`

.. _global-view-ref:

The Global Error View
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.globalerror

.. _list-wfs-ref:

List Workflows
~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.listpage

.. _workflow-view-ref:

Detailed Workflow View
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.seeworkflow

.. _getaction-ref:

Getting the List of Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.getaction

.. _reportaction-ref:

Reporting Completed Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.reportaction

.. _show-logs-ref:

Viewing Workflow Logs
~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.showlog

.. _new-user-ref:

Creating a New Account
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.newuser

.. _reset-pass-ref:

Reseting Account Password
~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.resetpassword

.. _manually-reset-cache-ref:

Manually Reseting Your Workflow Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.resetcache

.. _redo-cluster-ref:

Redoing the Workflow Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: workflowtools.WorkflowTools.cluster

.. _procedures-ref:


