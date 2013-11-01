#!/usr/bin/env python

import unittest
from octopshh import Octopshh, Ssh_conf, Ssh_host

TEST_1_CONFIG = """NoHostAuthenticationForLocalhost yes

ControlMaster auto 
ControlPath ~/.ssh/master-%r@%h:%p

IdentitiesOnly yes

Host _host1
	Hostname 10.0.0.1
	IdentityFile ~/.ssh/id_rsa_host1

Host _host2
	Hostname 10.0.0.2

Host _gateway1
##octopshh: pass:ssh-password/myhost
##octopshh: ^_host2:nc 127.0.0.1 3000
    Hostname 9.9.9.9
    User myuser
    Compression yes
"""

TEST_1_HOSTS = [
        Ssh_host("_host1", hostname="10.0.0.1", identityfile="~/.ssh/id_rsa_host1"),
        Ssh_host("_host2", hostname="10.0.0.2"),
        Ssh_host("_gateway1", hostname="9.9.9.9", user="myuser", compression="yes", octo_options="pass:ssh-password/myhost")
]

TEST_2_CONTENT = """Host _host1
	Hostname 10.0.0.1
	IdentityFile ~/.ssh/id_rsa_host1
"""

TEST_2_HOST = Ssh_host("_host1", hostname="10.0.0.1", identityfile="~/.ssh/id_rsa_host1")

class Octopshh_unittest(unittest.TestCase):
    def test_parse_cmdline(self):
        expected_ssh_hosts = ["_host1", "^", "_host2"]
        o = Octopshh(["_host1", "^", "_host2"], sshconf=Ssh_conf(content=TEST_1_CONFIG))
        self.assertEquals(o.targets, expected_ssh_hosts)

    @unittest.skip("IN PROGRESS")
    def test_build_connect_command(self):
        expected_connect_command = "ssh _host1"
        o = Octopshh(["_host1"], sshconf=Ssh_conf(content=TEST_1_CONFIG))
        o._build_connect_command()
        self.assertEquals(o.connect_command, expected_connect_command)

class Ssh_conf_unittest(unittest.TestCase):
    def test_parse_conf(self):
        expected_ssh_hosts = TEST_1_HOSTS
        conf = Ssh_conf(content=TEST_1_CONFIG)
        self.assertEqual(conf.hosts, expected_ssh_hosts)

class Ssh_host_unittest(unittest.TestCase):
    def test_parse(self):
        expected_host = TEST_2_HOST
        h = Ssh_host(content=TEST_2_CONTENT)
        self.assertEquals(h, expected_host)

if __name__ == "__main__":
    unittest.main()

