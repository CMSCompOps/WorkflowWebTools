import random
import uuid

for line in range(int(random.uniform(20, 50))):
    string = uuid.uuid4().hex
    print string[:22]
