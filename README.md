# UOMBooker

Python Code to Book Study Spaces

### **Example Usage:**

UOMBooker provides a high-level interface which allows bookings for study spaces to be completed with minimal commands.
In the example below a study space for AGLC will be booked for Monday morning:

```python
import uombooker
from uombooker.utils import Location, Session

booker = uombooker.Booker(location=Location.AGLC, session=Session.MonAM)
booker.book()
```

**Note:** The user must have stored their *MyManchester* credentials in the `config.yml` file.

### **Scheduling:**

One of the key advantages of UOMBooker is the ability to write scripts which book study spaces on a given schedule. This
can be done with the help of `cron`.

First develop a basic `BASH` script which takes care of running the Python code:

```bash
#!/bin/bash

# source the venv
source path/to/venv/bin/activate

# run the python
python path/to/python/code.py
```

Make sure to make the script executable:

```bash
$ chmod +x path/to/bash/script.sh
```

Enter `crontab` using:

```bash
$ crontab -e
```

Add a job to the scheduler:

```bash
0 0 * * FRI path/to/bash/script.sh
```

**Note:** Check to manual (`man crontab`) for help with setting a schedule.

###### Made by Daniel Kelshaw
