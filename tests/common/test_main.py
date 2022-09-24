# -*- coding: utf-8 -*-

import subprocess
import re

from clifs import __main__

PLUGINS_IMPLEMENTED =["backup","copy","del","du","move","ren","tree"]

def test_main(capfd):
    p = subprocess.run(["python", __main__.__file__, "-h"], capture_output=True)

    for plugin in PLUGINS_IMPLEMENTED:
        assert plugin in re.search(r"Available plugins:.*\n * \{([\w|,]*)\}", p.stdout.decode())[1]