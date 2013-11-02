#!/usr/bin/env python

# Octopshh - SSH bouncing helper
# 2013, Laurent Ghigonis <laurent@gouloum.fr>
# 2013, Pierre-Olivier Vauboin

import os
import re
import sys

class Octopshh(object):
    def __init__(self, targets, debug=False, sshconf=None):
        self.debug = debug
        self.sshconf = sshconf if sshconf else Ssh_conf()
        self.targets = targets
        if self.debug:
            print "octopshh: targets are %s" % self.targets

    def connect(self):
        self._build_connect_command()
        self._connect()

    def _build_connect_command(self):
        cmd = ""
        level=0
        next_transport = "ssh"
        for t in self.targets:
            if t == "^":
                next_transport = "ssh"
            else:
                # Parse host
                g = re.match(r'([^(^)]*)(\(.*\))*', t)
                if not g or len(g.groups()) != 2:
                    raise Exception("Invalid host %s" % t)
                h, o = g.groups()
                # Parse host options ()
                if o:
                    raise Exception("host options not implemented yet")
                if level == 0:
                    cmd += "%s %s" % (next_transport, h)
                else:
                    cmd += " -W %h:%p"
                    cmd = "%s %s -o ProxyCommand=\"%s\"" % (
                            next_transport, h,
                            cmd.replace("\"", "\\\""))
                level += 1
        self.connect_command = cmd

    def _connect(self):
        print self.connect_command
        os.system(self.connect_command)

class Ssh_conf(object):
    SSH_CONFIG = os.environ['HOME'] + "/.ssh/config"
    def __init__(self, content=None):
        if content:
            self.content = content.split('\n')
        else:
            f = open(self.SSH_CONFIG).readlines()
            self.content = [s.replace('\n', '') for s in f]
        # self.content : [ 'line1', 'line2', 'line3' ] # ssh config with no \n
        self._parse()

    def _parse(self):
        def __parse_host(content):
            h = Ssh_host(content=content)
            self.parsed.append(h)
            self.hosts.append(h)

        self.parsed = list()
        self.hosts = list()
        curhost = list()
        for line in self.content:
            if not curhost: # We are not in a Host section
                g = re.match(r'Host (.*)', line)
                if g:
                    curhost.append(line)
                else:
                    self.parsed.append(line)
            else: # We are in a Host section
                g = re.match(r'Host (.*)', line)
                if g:
                    __parse_host(curhost)
                    curhost = [line]
                else:
                    curhost.append(line)
        if curhost: # EOF and was in a Host section
            __parse_host(curhost)

class Ssh_host(object):
    RECOGNISED_OPTIONS = ['Hostname', 'IdentityFile', 'User', 'Compression']
    RECOGNISED_PATTERNS = ['Host'] + RECOGNISED_OPTIONS

    def __init__(self, host=None, hostname=None, identityfile=None,
            user=None, compression=None, octo_options=dict(),
            content=None, debug=False):
        self.debug = debug
        self.content = content
        self.host = host
        self.hostname = hostname
        self.identityfile = identityfile
        self.user = user
        self.compression = compression
        self.octo_options = octo_options
        if content:
            self.content = content.split('\n') if type(content) == str else content
            self._parse()

    def _parse(self):
        for line in self.content:
            if len(line) == 0:
                continue
            g = re.match(r'[\t ]*##octopshh: (.*):(.*)$', line)
            if g and len(g.groups()) == 2:
                t, v = g.groups()
                self.octo_options[t] = v
                continue
            g = re.match(r'[\t ]*([^ ]*) (.*)$', line)
            if not g or len(g.groups()) != 2:
                print "Ssh_host: _parse: invalid line, ignored: %s" % line
                continue
            n, v = g.groups()
            if n not in self.RECOGNISED_PATTERNS:
                print "Ssh_host: _parse: unknown line, ignored: %s" % line
                continue
            if self.debug:
                print "Ssh_host: _parse: %s = %s" % (n.lower(), v)
            setattr(self, n.lower(), v)

    def __eq__(self, other):
        for o in self.RECOGNISED_PATTERNS:
            if getattr(self, o.lower()) != getattr(other, o.lower()):
                return False
        return True

    def __str__(self):
        s =  "Host %s\n" % self.host
        for o in self.RECOGNISED_OPTIONS:
            if getattr(self, o.lower()):
                s += "  %s %s\n" % (o, getattr(self, o.lower()))
        return s

if __name__ == '__main__':
    octo = Octopshh(sys.argv[1:])
    octo.connect()
