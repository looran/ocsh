#!/usr/bin/env python

import paramiko

proxy = paramiko.ProxyCommand("nc 127.0.0.1 3333")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("127.0.0.1", username="laurent", password='none', sock=proxy)
client.close()
