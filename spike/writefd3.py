#!/usr/bin/env python3

import os
import subprocess

s = subprocess.run(["uname", "-a"], capture_output=True).stdout.decode().strip()
pr, pw = os.pipe()
os.set_inheritable(pr, True)
#os.set_inheritable(pw, True)
fdw = os.fdopen(pw, 'w')
print("writing to %d %s : %s" % (pw, fdw, s))
fdw.write(s)
fdw.close()
print("running subprocess with fd %s" % pr)
subprocess.run(f"read input<&{pr}; echo \"input: $input\"", shell=True, close_fds=False)
#os.system(f"read input<&{pr}; echo \"input: $input\"")
#os.system(f"read -u 3 input; echo \"input: $input\"")
