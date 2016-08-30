Workflow Team Web Tools
=======================

|build|

Welcome to the documentation for the new Workflow Team Web Tools.

Using the Web Tools
-------------------

Once you are pointed to a proper URL to access the webtools, you will
come to the home page, with links to different views.
For each of the examples below, I will use the base URL of ``https://localhost:8080/``,
since that is the URL you can see if you run the server on your machine.
If you are looking at a production server, the URL will of course be different.

Each page is a function of a ``WorkflowTools`` instance.
To pass parameters to the function, the usual urlencoding of the parameters
can be appended to the URL to call each function.
Most users should be able to interact with the website through their browser though.
From the URL root index, users will be able to directly access the following:

- :ref:`global-view-ref`
- :ref:`new-user-ref`
- :ref:`reset-pass-ref`
- :ref:`show-logs-ref`

.. _global-view-ref:
Global Error View
~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.globalerror

.. _workflow-view-ref:
Detailed Workflow View
~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.seeworkflow

.. _new-user-ref:
Creating a New Account
~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.newuser

.. _reset-pass-ref:
Reseting Account Password
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.resetpassword

.. _show-logs-ref:
Viewing Workflow Logs
~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.showlog

Running the Web Tools
---------------------

The webtools are operated behind a cherrypy server.

Running the Cherrypy Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. todo::
   Document a bash script!!

.. automodule:: workflowtools

.. automodule:: update_history

.. _server-config-ref:
Server Configuration
~~~~~~~~~~~~~~~~~~~~

The configuration file for the server is in ``YAML`` format.

Maintaining the Web Tools
-------------------------

Global Errors
~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.globalerrors
   :members:

Workflow Clustering
~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.clusterworkflows
   :members:

Manage Users
~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.manageusers
   :members:

Reasons Manipulation
~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.reasonsmanip
   :members:

Manage Actions
~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.manageactions
   :members:

Show Log
~~~~~~~~

.. automodule:: WorkflowWebTools.showlog
   :members:

WorkflowWebTools Forks' Build Statuses
--------------------------------------

If you have a fork with automated build tests set up
(see :ref:`tests-ref`), then feel free to add your badge here for easy viewing.

dabercro: |build-dabercro|

.. |build-dabercro| image:: https://travis-ci.org/dabercro/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/dabercro/WorkflowWebTools

.. |build| image:: https://travis-ci.org/CMSCompOps/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/CMSCompOps/WorkflowWebTools
