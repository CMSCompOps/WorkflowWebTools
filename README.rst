Workflow Team Web Tools
=======================

|build|

Welcome to the documentation for the new Workflow Team Web Tools.

Using the Web Tools
-------------------

Once you are pointed to a proper URL to access the webtools, you will
come to the home page, with links to different views.
To view logs from our elastic search service,
look at `Show Logs`_.
To get an overall picture of the errors occurring at sites,
look at the `Global Error View`_.
To get the JSON file containing the actions that will be done by Unified,
look at `Get Latest Actions`_.

For each of the examples below, I will use the base URL of ``localhost:8080``,
since that is the URL you can see if you run the server on your machine.

Show Logs
~~~~~~~~~

Global Error View
~~~~~~~~~~~~~~~~~

Get Latest Actions
~~~~~~~~~~~~~~~~~~~

Running the Web Tools
---------------------

The webtools are operated behind a cherrypy server.

Maintaining the Web Tools
-------------------------

Show Log
~~~~~~~~

.. automodule:: WorkflowWebTools.showlog
   :members:

Global Errors
~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.globalerrors
   :members:

Reasons Manipulation
~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.reasonsmanip
   :members:

.. |build| image:: https://travis-ci.org/CMSCompOps/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/CMSCompOps/WorkflowWebTools
