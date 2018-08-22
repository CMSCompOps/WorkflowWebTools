Workflow Team Web Tools
=======================

|build|

Welcome to the documentation for the new Workflow Team Web Tools.

.. contents:: :local:

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

Workflows Procedures
--------------------

.. automodule:: WorkflowWebTools.procedures

Running the Web Tools
---------------------

The webtools are usually operated behind a cherrypy server.
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

If you need sudo privileges, to access a certain port for example,
you can use the script::

    ./run.sh

You may need to adjust the values in ``runserver/setenv.sh`` first.

Running the Server Behind WSGI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If running the site in a production environment,
you will likely need to run behind WSGI to enable CERN's SSO.
Install ``mod_wsgi``, which is not listed as a strict requirement for the package.

In your apache configuration, create a virtual host for the WSGI application.
You will also need to allow access to the ``runserver/static`` directory.
An example would be as follows::

    Listen 443
    <VirtualHost *:443>
        WSGIScriptAlias / <path_to_WorkflowWebTools>/runserver/workflowtools.py

        Alias /static <path_to_WorkflowWebTools>/runserver/static

        <Directory <path_to_WorkflowWebTools>/runserver>

            #
            # Add Shibboleth authentification here? (Not developed yet)
            #

            WSGIApplicationGroup %{GLOBAL}
            <IfVersion >= 2.4>
                Require all granted
            </IfVersion>
            <IfVersion < 2.4>
                Order allow,deny
                Allow from all
            </IfVersion>

        </Directory>

        ServerName 127.0.0.1
        SSLEngine on
        SSLCertificateFile <path_to_cert>
        SSLCertificateKeyFile <path_to_private_key>

    </VirtualHost>

.. Note::

   This is just what I have working on my laptop.
   This website has not been run behind WSGI in production yet.
   I would be grateful to learn about any errors in this section of the documentation.

Predicting Actions with SciKit-Learn
------------------------------------

There have been some preliminary attempts to create a model that predicts actions
on a workflow based on the errors that it throws.
The results of this preliminary training are presented in the slides located at
``WorkflowWebTools/docs/170705/dabercro_WorkflowWebTools_170705.pdf``.

The following are instructions to run the training and test interactively:

- First, create a JSON file that contains all of features and actions of previous workflows.
  This can be done with the script located at ``WorkflowWebTools/runserver/create_actionshistorylink.py``::

      ./create_actionshistorylink.py static/history.VERSION_NUMBER.json

  This should be done from the production server.
  The argument is just the name of the output file.

- Then download the output JSON file to the computer where you will be doing the training.
  The module :py:mod:`WorkflowWebTools.paramsregression` also contains a script for running the training interactively.
  This can be run from inside the ``WorkflowWebTools`` directory with the following::

      python2.7 paramsregression.py PATH/TO/history.VERSION_NUMBER.json

  By default, this will train for the ``'action'`` field.
  To train a different parameter, give another argument to the script::

      python2.7 paramsregression.py PATH/TO/history.VERSION_NUMBER.json memory

The easiest way to get the classifier from inside server would be to call something like the following::

    from WorkflowWebTools import actionshistorylink
    from WorkflowWebTools import paramsregression

    model = paramsregression.get_classifier(actionshistorylink.dump_json(), 'action')

The clusterer then works like any other ``sklearn`` trained model.

.. Note::
   This may take a long time to return, so generating the classifier
   is only something you would want to do once in a while
   (such as when the server first turns on or when an approved
   user accesses some restricted address).

For more details on the fuctions used in the internals, see :ref:`ml-ref` (or the source code).

Troubleshooting
---------------

This is just a quick guide for anyone trying to troubleshoot or restart the production server.

If the web service is not responding,
first check that you are accessing the machine using CERN's network
(either by being physically at CERN or using a proxy).
If you are certain that you are using the CERN network, then you will have to log into the server.
The name of the server is not given due to potential security concerns.
To complete all of the following steps, you need sudo access to the machine.

 #. SSH into a CERN machine.
 #. Try downloading actions from the machine::

        wget -O test.json --no-check-certificate "https://vocms0113.cern.ch/getaction?days=30&acted=-1"

    If the file ``test.json`` is not empty, then the service is likely still running properly.
    Go back to checking your own connection.
 #. SSH into the server from LXPLUS::

        ssh vocms0113

 #. Check the process ID and see if it is still running::

        # This shows the PID
        cat /home/dabercro/OpsSpace/WorkflowWebTools/runserver/pid
        # This checks what processes are running with name 'python2.7'
        pgrep python2.7

 #. The cache may be in the process of updating.
    You can check this with the following::

        ls -ltr /tmp/workflowinfo/ | tail

    If those are recent (more recent than when the server stopped responding), then the cache is being rebuilt.

 #. If it is running, the cache is not being rebuilt, and the server is still definitely not responding, kill the process::

        sudo kill -9 $(cat /home/dabercro/OpsSpace/WorkflowWebTools/runserver/pid)

 #. Do the following to start the process again::

        cd /home/dabercro/OpsSpace/WorkflowWebTools/runserver
        ./run.sh

 #. Check the server status::

        sudo tail -f /home/dabercro/OpsSpace/WorkflowWebTools/runserver/nohup.out

    (You can exit ``tail`` with ``Ctrl + c``.) Hopefully, the last line eventually says something like::

        ENGINE Bus STARTED

    If this is taking a long time to show up,
    It is likely rebuilding the cache.
    You can check this as mentioned above::

        ls -ltr /tmp/workflowinfo/ | tail

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

.. _clustering-ref:

Workflow Info
~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.workflowinfo
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

Classifying Errors
~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.classifyerrors
   :members:

List Workflows At Site
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.listpage
   :members:

.. _ml-ref:

Machine Learning Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: WorkflowWebTools.actionshistorylink
   :members:

.. automodule:: WorkflowWebTools.paramsregression
   :members:

JavaScript and Mako User Interface
----------------------------------

Some documentation of the JavaScript used on the webpages are given below.

.. autoanysrc:: phony
   :src: ../WorkflowWebTools/runserver/static/js/*.js
   :analyzer: js

.. |build| image:: https://travis-ci.org/CMSCompOps/WorkflowWebTools.svg?branch=master
    :target: https://travis-ci.org/CMSCompOps/WorkflowWebTools

.. |br| raw:: html

   <br>
