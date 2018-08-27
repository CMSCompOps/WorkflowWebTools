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
   :src: ../runserver/setup_server.sh
   :analyzer: shell-script

Server Configuration
~~~~~~~~~~~~~~~~~~~~

.. autoanysrc:: dummy
   :src: ../test/config.yml
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


