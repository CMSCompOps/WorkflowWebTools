workflowmonit
-------------

Component which periodically fetches information of workflows in the system(list extracted from Unified database), process and organizes into static documents, then sends to CMSMONIT service via :py:mod:`CMSMonitoring.StompAMQ` for storage, monitoring and post-aggregation.

- :ref:`usedApi-ref`
- Composition
    - :ref:`wmCollector-ref`
    - :ref:`wmSender-ref`
    - :ref:`wmScheduler-ref`
- :ref:`wmDocExample-ref`

.. _usedApi-ref:

Used APIs
~~~~~~~~~

- wmstatserver:
    - https://cmsweb.cern.ch/wmstatsserver/data/jobdetail/
    - https://cmsweb.cern.ch/wmstatsserver/data/request/
- couchdb:
    - https://cmsweb.cern.ch/couchdb/acdcserver/_design/ACDC/_view/byCollectionName/


.. _wmCollector-ref:

workflowCollector
~~~~~~~~~~~~~~~~~

.. automodule:: workflowmonit.workflowCollector
   :members:


.. _wmSender-ref:

sendToMonit
~~~~~~~~~~~

.. automodule:: workflowmonit.sendToMonit
   :members:


.. _wmScheduler-ref:

workflowMonitScheduler
~~~~~~~~~~~~~~~~~~~~~~

Schedule the ``main`` function of :ref:`wmSender-ref` every hour with :py:mod:`schedule`::

    import workflowmonit.sendToMonit as wms
    schedule.every().hour.do(wms.main)
    while True:
        schedule.run_pending()
        time.sleep(1)


.. _wmDocExample-ref:

Document examples
~~~~~~~~~~~~~~~~~

1. document describling a single workflow `example1 <http://wsi.web.cern.ch/wsi/public/toSaveExample4.json>`_
2. document wrapped by ``StompAMQ`` as a batch `example2.1 <http://wsi.web.cern.ch/wsi/public/godummy2.json>`_, `example2.2 <http://wsi.web.cern.ch/wsi/public/amqMsg_190208-201142.json>`_
3. document sent out by ``stomp`` (what ``StompAMQ`` wrapped around) `example3 <http://wsi.web.cern.ch/wsi/public/bab2ef60-b0f2-4b55-9434-95a9cfd00510.json>`_
