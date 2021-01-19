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

        wget -O test.json --no-check-certificate "https://wfrecovery.cern.ch/getaction?days=30&acted=-1"

    If the file ``test.json`` is not empty, then the service is likely still running properly.
    Go back to checking your own connection.
 #. SSH into the server from LXPLUS::

        ssh wfrecovery

 #. Check the process ID and see if it is still running::

        # This shows the PID
        cat /home/console/runserver/pid
        # This checks what processes are running with name 'workflowtool'
        pgrep workflowtool

 #. The cache may be in the process of updating.
    You can check this with the following::

        ls -ltr /tmp/workflowinfo/ | tail

    If those are recent (more recent than when the server stopped responding), then the cache is being rebuilt.

 #. If it is running, the cache is not being rebuilt, and the server is still definitely not responding, kill the process::

        sudo kill -9 $(cat /home/console/runserver/pid)

 #. Do the following to start the process again::

        cd /home/console/runserver/
        nohup ./run.sh &

 #. Check the server status::

        sudo tail -f /home/console/runserver/nohup.out

    (You can exit ``tail`` with ``Ctrl + c``.) Hopefully, the last line eventually says something like::

        ENGINE Bus STARTED

    If this is taking a long time to show up,
    It is likely rebuilding the cache.
    You can check this as mentioned above::

        ls -ltr /tmp/workflowinfo/ | tail


