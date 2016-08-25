Workflow Team Web Tools
=======================

|build|

Welcome to the documentation for the new Workflow Team Web Tools.

Using the Web Tools
-------------------

Once you are pointed to a proper URL to access the webtools, you will
come to the home page, with links to different views.
To view logs from our elastic search service,
look at :ref:`show-ref`.
To get an overall picture of the errors occurring at sites,
look at :ref:`global-view-ref`.
To get the JSON file containing the actions that will be done by Unified,
look at :ref:`actions-ref`.

For each of the examples below, I will use the base URL of ``localhost:8080``,
since that is the URL you can see if you run the server on your machine.

.. _show-ref:

Show Logs
~~~~~~~~~

.. _global-view-ref:

Global Error View
~~~~~~~~~~~~~~~~~

.. _actions-ref:

Get Latest Actions
~~~~~~~~~~~~~~~~~~~

Running the Web Tools
---------------------

The webtools are operated behind a cherrypy server.

Maintaining the Web Tools
-------------------------

Script to Run Cherrypy Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: workflowtools
   :members:

Show Log
~~~~~~~~

.. automodule:: WorkflowWebTools.showlog
   :members:

Global Errors
~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.globalerrors
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
~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.manageactions
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
