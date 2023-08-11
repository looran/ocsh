#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

path_src = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(path_src))
import ocsh

file = Path(__file__).resolve().parent.parent / "README.md"

p = subprocess.run([path_src / "ocsh.py", "-h"], stdout=subprocess.PIPE)
usage = p.stdout.decode()

readme = """## {desc}

{summary}

## Usage
```
{usage}
```

## Installation

```
pip install ocsh
```

## Examples of usage
```
{examples}
```

## See also

* netmiko - python library to SSH to various network devices
  https://github.com/ktbyers/netmiko
* sshpass - automate SSH password-based log-in
  https://github.com/kevinburke/sshpass
* passh - sshpass alternative to automate SSH password-based log-in
  https://github.com/clarkwang/passh
""".format(desc=ocsh.DESCRIPTION,
    summary=ocsh.SUMMARY.split("\n\nv2")[0],
    usage=usage.split("\n\nocsh automates SSH")[0],
    examples=ocsh.EXAMPLES)

file.write_text(readme)

print("[*] DONE, wrote %s" % file)
