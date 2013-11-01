#!/usr/bin/env python

# from http://stackoverflow.com/questions/1911690/nested-ssh-session-with-paramiko
# modified to use sshkey

import paramiko as ssh

class SSHTool():
    def __init__(self, host, user, key,
                 via=None, via_user=None, via_key=None):
        if via:
            t0 = ssh.Transport(via)
            t0.start_client()
            via_key_class = ssh.RSAKey.from_private_key_file(via_key)
            t0.auth_publickey(via_user, via_key_class)
            # setup forwarding from 127.0.0.1:<free_random_port> to |host|
            channel = t0.open_channel('direct-tcpip', host, ('127.0.0.1', 0))
            self.transport = ssh.Transport(channel)
        else:
            self.transport = ssh.Transport(host)
        self.transport.start_client()
        key_class = ssh.RSAKey.from_private_key_file(key)
        self.transport.auth_publickey(user, key_class)

    def run(self, cmd):
        ch = self.transport.open_session()
        ch.set_combine_stderr(True)
        ch.exec_command(cmd)
        retcode = ch.recv_exit_status()
        buf = ''
        while ch.recv_ready():
            buf += ch.recv(1024)
        return (buf, retcode)

# The example below is equivalent to
# $ ssh 10.10.10.10 ssh 192.168.1.1 uname -a
# The code above works as if these 2 commands were executed:
# $ ssh -L <free_random_port>:192.168.1.1:22 10.10.10.10
# $ ssh 127.0.0.1:<free_random_port> uname -a
ssht = SSHTool(('X.X.X.X', 22), 'laurent', '/home/laurent/.ssh/id_rsa_X',
    via=('Y.Y.Y.Y', 22), via_user='root', via_key='/home/laurent/.ssh/id_rsa_Y')

print ssht.run('uname -ap')
