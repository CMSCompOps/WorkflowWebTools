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

    from workflowwebtools import actionshistorylink
    from workflowwebtools import paramsregression

    model = paramsregression.get_classifier(actionshistorylink.dump_json(), 'action')

The clusterer then works like any other ``sklearn`` trained model.

.. Note::
   This may take a long time to return, so generating the classifier
   is only something you would want to do once in a while
   (such as when the server first turns on or when an approved
   user accesses some restricted address).

For more details on the fuctions used in the internals, see :ref:`ml-ref` (or the source code).

