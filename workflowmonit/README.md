workflowmonit
=============

Component which uploads some workflow information to CMSMONIT service for storage and monitoring.

- It extracts interested workflow list from Unified database,
- downloads caches from wmstatserver,
- filters and structurizes information into a static document [example](http://wsi.web.cern.ch/wsi/public/toSaveExample4.json),
- and send out messages [example](http://wsi.web.cern.ch/wsi/public/godummy2.json).
