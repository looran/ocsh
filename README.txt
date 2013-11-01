Octopshh - SSH bouncing helper
2013, Laurent Ghigonis <laurent@gouloum.fr>
2013, Pierre-Olivier Vauboin

Et op !
Pronounce 'OctoPshii'

WARNING: WORK IN PROGRESS - 20131101 laurent
DO NOT EXPECT THIS TO WORK !!!


Example usage
=============

Connect to _host2, bouncing on _host1 (_host1 and _host2 already in ssh_config)
op _host1 ^ _host2
## Equivalent SSH command:
## ssh _host2 -o ProxyCommand="ssh _host1 -W %h:%p"

Connect to _host2, bouncing on different _host1 IP address
op _host1(10.0.0.1) ^ _host2
## Equivalent SSH command:
## ssh -o ProxyCommand="ssh _host1 -W %h:%p"

Connect to _host2, bouncing on different _host1 IP address + login + pass
op _host1(laurent:pass-sshpass/host1@10.0.0.1) ^ _host2
## Equivalent SSH command:
## ssh _host2 -o ProxyCommand="ssh -o User=laurent -o PasswordAuthentication=yes _host1 -W %h:%p"
## "pexpect" will be used to give the password to SSH from "pass"

Connect to host2, bouncing on particular IP+port of _host1
op _host1 ^ _host2(127.0.0.1 4141)
## Equivalent SSH command:
## ssh -o HostName=127.0.0.1 _host2 -o ProxyCommand="ssh _host1 -W 127.0.0.1:4141"

Connect to host2, bouncing on particular IP+port of _host1 and setting this as
default behavior when comming from _host1
op _host1 ^ _host2(127.0.0.1 4141 def)
## Equivalent SSH command:
## ssh -o HostName=127.0.0.1 _host2 -o ProxyCommand="ssh _host1 -W 127.0.0.1:4141"
## and your ssh_config will get updated with "##octopshh: _host1^:127.0.0.1 4141" in _host2
## so next time when you come from _host1 it will be the default

Connect to host2, bouncing on normal _host1 IP+port
op _host1 ^ _host2()
## Equivalent SSH command:
## ssh _host2 -o ProxyCommand="ssh _host1 -W %h:%p"


ssh_config auto update
======================

New host: host(IP [port])
Everytime a commandline configuration is specified with () for connecting to
a host, and host does not exist in ssh_config, it will be automaticaly added
by Octopshh.

New default: host(IP [port] def)
If the host exists in ssh_config, and the keyword 'def' is used in the
commandline configuration using (), ssh_config will be updated


Octopshh special options in ssh_config
======================================

Host _host2
    ##octopshh: pass:ssh-password/myhost
    ##octopshh: _host1^:127.0.0.1 4141



======================================
              ======
               TODO
              ======


TODO: Using directly the SSH command
====================================

Pros:
* possible more readable
* can echo the command to connect without Octopshh

Cons:
* manual redo of sshkey decrypt / ssh-agent
* manual tunnels


TODO: Support for mosh
======================

Connect to _host2, bouncing on _host1 and using mosh between _host1 and _host2
op _host1 ^^ _host2

Starts mosh-server on _host2, and mosh-client on _host1.
Normal SSH is used to _host1
Of course 

Bounce by _host0
op _host0 ^ _host1 ^^ _host2

Use mosh for the first hop
op && _host0 ^ _host1 ^ _host2

Ressources
http://samy.pl/pwnat/
https://github.com/keithw/mosh/issues/285
udp inside tcp tunnel: http://www.cs.columbia.edu/~lennox/udptunnel/

