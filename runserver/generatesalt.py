"""
Importing or running this module will output a list of random strings
to be used as salt values for hashing the database entries.
This is used for :ref:`server-config-ref`.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import random
import uuid

for line in range(int(random.uniform(20, 50))):
    string = uuid.uuid4().hex
    print string[:22]
