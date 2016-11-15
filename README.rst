Workflow Team Web Tools
=======================

|build|

Welcome to the documentation for the new Workflow Team Web Tools.

.. contents:: :local:

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

The Global Error View
~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.globalerror

.. _workflow-view-ref:

Detailed Workflow View
~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.seeworkflow

.. _getaction-ref:

Getting the List of Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.getaction

.. _reportaction-ref:

Reporting Completed Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.reportaction

.. _show-logs-ref:

Viewing Workflow Logs
~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.showlog

.. _new-user-ref:

Creating a New Account
~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.newuser

.. _reset-pass-ref:

Reseting Account Password
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.resetpassword

.. _manually-reset-cache-ref:

Manually Reseting Your Workflow Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.resetcache

.. _redo-cluster-ref:

Redoing the Workflow Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosimple:: workflowtools.WorkflowTools.cluster

Running the Web Tools
---------------------

The webtools are operated behind a cherrypy server.
Before running the script ``runserver/workflowtools.py``,
there are a few other things that you should set up first.

.. _server-config-ref:

Setting Up Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first script you should run is ``setup_server.sh``.
Run this from inside the ``runserver`` directory::

    cd runserver
    ./setup_server.sh

.. autoanysrc:: dummy
   :src: ../WorkflowWebTools/runserver/setup_server.sh
   :analyzer: shell-script

Server Configuration
~~~~~~~~~~~~~~~~~~~~

.. autoanysrc:: dummy
   :src: ../WorkflowWebTools/test/config.yml
   :analyzer: shell-script

Updating the Error History
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: update_history

Starting the CherryPy Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, the service can be launched by running::

    ./workflowtools.py

.. automodule:: workflowtools

If you need sudo privileges, to access a certain port for example,
you can use the script::

    ./run.sh

.. autoanysrc:: dummy
   :src: ../WorkflowWebTools/test/config.yml
   :analyzer: shell-script

Running the Server Behind WSGI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If running the site in a production environment,
you will likely need to run behind WSGI to enable CERN's SSO.
Install ``mod_wsgi`` with the following::

    pip install mod_wsgi

This is not listed as a strict requirement for the package.

.. todo::

   Place documentation on how to configure the httpd service...

Maintaining the Python Backend
------------------------------

For developers wishing to make adjustments to the modules or
anyone else who wants to understand some of the backend of the server,
all of the Python modules for this system are documented below.

Server Configuration
~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.serverconfig
   :members:

Functions for Error Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.errorutils
   :members:

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

JavaScript and Mako User Interface
----------------------------------

Some documentation of the JavaScript used on the webpages are given below.

.. autoanysrc:: phony
   :src: ../WorkflowWebTools/runserver/static/js/*.js
   :analyzer: js

WorkflowWebTools Forks' Build Statuses
--------------------------------------

If you have a fork with automated build tests set up
(see :ref:`tests-ref`), then feel free to add your badge here for easy viewing.

dabercro: |build-dabercro|

.. |build-dabercro| image:: https://travis-ci.org/dabercro/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/dabercro/WorkflowWebTools

.. |build| image:: https://travis-ci.org/CMSCompOps/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/CMSCompOps/WorkflowWebTools
