#!/usr/bin/env python3

# 2013, 2023 Laurent Ghigonis <ooookiwi@gmail.com>
# 2013, Pierre-Olivier Vauboin

DESCRIPTION = "ocsh - SSH password log-in and command automator"
VERSION = "20230908-3"
SUMMARY = f"""ocsh automates SSH password login and command execution through annotations on `ssh_config(5)` Hosts:
* password authentication, reading password from pass[1]:
  - config:  `# ocsh pass <pass-name>`
  - command: `$ ocsh host`
* post-login command execution:
  - config:  `# ocsh post <action> "<cmd>"`
  - command: `$ ocsh host[action]`
* post-login command execution, reading additional password from pass[1]:
  - config:  `# ocsh postpass <action> "<cmd>" <pass-name>`
  - command: `$ ocsh host[action]`
* use different ssh command or prefix by other command:
  - config:  `# ocsh cmd "<ssh-command>"`
  - config:  `# ocsh pre "<pre-command>"`
  - command: `$ ocsh host`

[1] https://www.passwordstore.org/

Compatibility with OpenSSH is kept as much as possible:
* support usual SSH aliases, keys and command-line options
* compatible with rsync, scp and other tools using SSH for transport, see example commands
* autocompletion can be set-up with --ocsh-install-autocompletion

v{VERSION}
See also --ocsh-examples
"""
EXAMPLES = """# connect to SSH alias 'host1' with automated password login
# ssh_config(5)
Host host1
   Hostname 10.0.0.1
   User minou
   # ocsh pass pass-location                 # location in password-store
# command
ocsh host1
# equivalent ssh command
sshpass -p "$(pass pass-location)" ssh host1

# connect to SSH alias 'host2' with automated password login, going through the above 'host1', and become root
# ssh_config(5)
Host host2
    Host 10.9.0.1
    User root
    # ocsh pass pass-location2               # location in password-store
    # ocsh postpass su "su -l" pass-location3
    # ocsh post nsep "ip netns exec nsep"    # post-login command to enter a network namespace
# command
ocsh host2[root]
# equivalent ssh command
sshpass -p "$(pass pass-location2)" ssh -oProxyCommand="sshpass -p "$(pass pass-location1)" ssh host1" host2 su -l
<now enter root password (from pass-location3) manually>

# run ssh connection from a different namespace
# ssh_config(5)
Host host1
   Hostname 10.0.0.1
   User minou
   # ocsh pre "ip netns exec toto"
# command
ocsh host1
# equivalent command
ip netns exec ssh host1

# run rsync through ocsh from host1 with automated password login
rsync -e "ocsh" -avP host1:/etc/hosts /tmp/

# run scp through ocsh from host1 with automated password login
scp -S "ocsh" host1:/etc/hosts /tmp/"""

import os
import re
import sys
import shutil
import logging
import tempfile
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
from logging import info, debug, warning, error

import pexpect

class Sshconf(object):
    CONFPATH_DEFAULT = Path.home() / ".ssh/config"

    def __init__(self, conf_path):
        self.conf_path = conf_path
        self.main = dict()
        self.hosts = dict()
        self._load(conf_path)

    def _load(self, conf_path):
        if not conf_path.exists():
            return

        current = "main"
        for numline, line in enumerate(conf_path.read_text().split("\n")):
            line = line.strip()
            if not line:
                continue

            # parse commented line
            if line.startswith('#'):
                cline = line[1:].strip()
                if cline.startswith("ocsh"):
                    if current == "main":
                        m = re.match(r"ocsh(?:\s*=\s*|\s+)pass-executable(?:\s*=\s*|\s+)(?P<pass-cmd>.+)", cline)
                        if m:
                            self.main['pass-executable'] = m['pass-cmd']
                            continue
                    m = re.match(r"ocsh(?:\s*=\s*|\s+)cmd(?:\s*=\s*|\s+)(?P<cmd>.+)", cline)
                    if m:
                        self.hosts[current]['cmd'] = m['cmd']
                        continue
                    m = re.match(r"ocsh(?:\s*=\s*|\s+)pre(?:\s*=\s*|\s+)(?P<pre>.+)", cline)
                    if m:
                        self.hosts[current]['pre'] = m['pre']
                        continue
                    m = re.match(r"ocsh(?:\s*=\s*|\s+)pass(?:\s*=\s*|\s+)(?P<passname>.+)", cline)
                    if m:
                        self.hosts[current]['pass'] = m['passname']
                        continue
                    m = re.match(r"ocsh(?:\s*=\s*|\s+)post(?:\s*=\s*|\s+)(?P<action>[\w\_-]+)(?:\s*=\s*|\s+)(?P<cmd>.+)", cline)
                    if m:
                        cmd = m['cmd'].strip('"')
                        self.hosts[current]['post'][m['action']] = [cmd, None]
                        continue
                    m = re.match(r"ocsh(?:\s*=\s*|\s+)postpass(?:\s*=\s*|\s+)(?P<action>[\w\_-]+)(?:\s*=\s*|\s+)(?P<arg>.+)", cline)
                    if m:
                        r = m['arg'].rsplit(' ', 1)
                        if len(r) == 2:
                            cmd = r[0].strip('"')
                            passname = r[1].strip('"')
                            self.hosts[current]['post'][m['action']] = [cmd, passname]
                            continue
                    self._warn("could not parse ocsh annotation", current, numline, line)
                continue

            # parse normal line
            m = re.match(r"(?P<option>\w+)(?:\s*=\s*|\s+)(?P<arg>.+)", line)
            if m:
                if m['option'] == 'Host':
                    current = m['arg']
                    self.hosts[current] = defaultdict(dict)
                else:
                    if m['option'] == "Include":
                        self._load(Path(m['arg']))
                    elif current == "main":
                        self.main[m['option']] = m['arg']
                    else:
                        self.hosts[current][m['option']] = m['arg']
                continue
            self._warn("could not parse line", current, numline, line)

    def _warn(self, text, current, numline, line):
        warning("warning: ssh_config:%d %s%s: %s" % (numline, text, "" if current == "main" else " in Host %s" % current,  line))
        

class Octossh(object):
    AUTOCOMPLETION = """_ocsh()
{
    local cur prev words cword
    _init_completion -n : || return
    _expand || return
    [[ $cur == @(*/|[.~])* ]] || _known_hosts_real -c -a -- "$cur"
} && complete -F _ocsh -o nospace ocsh
"""

    @classmethod
    def install_bash_completion(cls):
        f = Path.home() / ".bash_completion"
        if f.exists():
            s = f.read_text()
            if "_ocsh" in s:
                print("error: _ocsh autocompletion function already found in %s" % f)
                sys.exit(1)
        else:
            s = ""
        s += Octossh.AUTOCOMPLETION
        f.write_text(s)
        print("_ocsh autocompletion function added to %s" % f)

    def __init__(self, conf, destination, jumphosts=None, args=None, ssh_options=None):
        if shutil.which('ssh') is None:
            raise self._err("you must install 'ssh'")
        self.conf = conf
        self.prog = str(Path(sys.argv[0]))
        if self.conf.conf_path:
            self.prog += " -F %s" % self.conf.conf_path

        ssh_cmd, ssh_target, post, conf = self._get_target_cmd(destination)
        debug(f"destination={destination} args={args} ssh_cmd={ssh_cmd} ssh_target={ssh_target} post={post} conf={conf}")

        # construct imbricated proxycommand SSH commands for all target
        if jumphosts:
            self._err("-J support not implemented")
            # XXX TODO implement jump host properly
            jump_list = jumphosts.split(',')
            cmd = ""
            for idx, host in enumerate(jump_list):
                cmd = "ssh -o ProxyCommand=\"{} -W %h:%p {}\"".format(cmd.replace("\"", "\\\""), host)
            ssh_cmd = "{} -o ProxyCommand=\"{}\"".format(ssh_cmd, cmd)
            #cmd = ""
            #for idx, target in enumerate(targets_list):
            #    ssh_cmd, ssh_target, post = self._get_target_cmd(target)
            #    if ssh_options and idx == len(targets_list) - 1: # insert provided ssh_options only for first-level command, meaning last target
            #        ssh_cmd = ssh_cmd + ' ' + ' '.join(ssh_options)
            #        ssh_options = None
            #    if len(cmd) > 0:
            #        cmd = "{} -o ProxyCommand=\"{} -W %h:%p\" {}".format(ssh_cmd, cmd.replace("\"", "\\\""), ssh_target)
            #    else:
            #        cmd = "{} {}".format(ssh_cmd, ssh_target)

        self.ssh_target = ssh_target
        self.ssh_command = "{} {}".format(ssh_cmd, ssh_target)
        if args:
            debug(f"adding command args: '{args}'")
            self.ssh_command += f" '{args}'"
        self.post = post
        self.conf = conf

    def run(self):
        ssh_command = self.ssh_command
        fpass = None
        if 'pass' in self.conf:
            if shutil.which('pass') is None:
                raise self._err("you must install 'pass', see https://www.passwordstore.org/")
            if shutil.which('sshpass') is None:
                raise self._err("you must install 'sshpass'")

            stricthostkeychecking = subprocess.run(f"ssh -G {self.ssh_target} |grep '^stricthostkeychecking ' |cut -d' ' -f2", shell=True, capture_output=True).stdout.decode().strip()
            if stricthostkeychecking == 'yes':
                debug("checking if target server public key is in ssh known_hosts")
                hostname = subprocess.run(f"ssh -G {self.ssh_target} |grep '^hostname ' |cut -d' ' -f2", shell=True, capture_output=True).stdout.decode().strip()
                check_res = subprocess.run(["ssh-keygen", "-l", "-F", hostname], capture_output=True)
                if check_res.returncode == 1:
                    # we cannot use ssh-keyscan when a proxy is involved, since ssh-keyscan does not respect ProxyJump / ProxyCommand
                    self._err("fingerprints of SSH host '%s' not found !\nUse normal ssh(1) to accept the keys, or StrictHostKeyChecking in ssh_config(5)" % self.ssh_target)

            debug("setting-up sshpass using named pipe")
            password = subprocess.run(["pass", self.conf['pass']], capture_output=True).stdout.strip()
            if len(password) == 0:
                self._err("pass: password not found for host %s : %s" % (self.ssh_target, self.conf['pass']))
            fpass = Path(tempfile.mkdtemp()) / "fifo"
            os.mkfifo(fpass)
            fr = os.open(fpass, os.O_RDONLY | os.O_NONBLOCK)
            fw = os.open(fpass, os.O_WRONLY)
            os.write(fw, password)
            os.write(fw, b'\n')
            ssh_command = "sshpass -f{} {} ".format(fpass, ssh_command)

        if 'pre' in self.conf:
            ssh_command = self.conf['pre'] + " " + ssh_command

        debug("running: %s" % ssh_command)

        if len(self.post.keys()) > 0:
            if not os.isatty(sys.stdout.fileno()):
                raise self._err("cannot use post actions in non-interactive shell")
            p = pexpect.spawn(ssh_command)
            for action in self.post.keys():
                cmd, passname = self.post[action]
                debug("post action : %s" % cmd)
                p.sendline(cmd)
                if passname:
                    try:
                        p.expect("\n", timeout=10)
                    except Exception as e:
                        self._err("timeout waiting for shell in post action %s:\n%s" % (action, e))
                    if shutil.which('pass') is None:
                        raise self._err("you must install 'pass', see https://www.passwordstore.org/")
                    password = subprocess.run(["pass", passname], capture_output=True).stdout.decode().strip()
                    if len(password) == 0:
                        self._err("pass: password not found for host %s, post action %s : %s" % (self.ssh_target, cmd, passname))
                    try:
                        p.expect("[Pp]assword[^:]*:", timeout=5)
                    except Exception as e:
                        self._err("timeout waiting for password in post action '%s':\n%s" % (action, e))
                    p.sendline(password)
            p.interact()
        else:
            subprocess.run(ssh_command, shell=True)

        if fpass:
            debug("removing password fifo %s" % fpass)
            fpass.unlink()
            fpass.parent.rmdir()

    def _get_target_cmd(self, target):
        # read user provided target and options
        usr = re.match(r"((?P<user>\w+)@)?(?P<host>\w+)(\[(?P<post>.*)\])?", target).groupdict()
        target = target.rsplit('[', 1)[0] # remove post-login actions from target command-line

        # if host in configuration, read parameters not yet existing
        conf = dict()
        post = dict()
        if usr['host'] in self.conf.hosts:
            conf = self.conf.hosts[usr['host']]
            if usr['post']:
                for action in usr['post'].split(','):
                    if action in conf['post']:
                        post[action] = conf['post'][action]
                    else:
                        raise self._err("invalid action '%s' for host '%s'" % (action, usr['host']))
                
        # construct command to reach target
        if 'cmd' in conf:
            ssh_cmd = conf['cmd']
        else:
            ssh_cmd = "ssh"
        if logging.root.level == logging.DEBUG:
            ssh_cmd += " -v"
        if self.conf.conf_path:
            ssh_cmd += " -F %s" % self.conf.conf_path
        if 'ProxyJump' in conf:
            # if ProxyJump in ssh_config(5), replace with ocsh
            ssh_cmd += ' -o ProxyCommand="{} -W %h:%p {}" -o ProxyJump=None'.format(self.prog, conf['ProxyJump'])
        elif 'ProxyCommand' in conf:
            # if ProxyCommand in ssh_config(5) uses ssh, replace with ocsh
            pcmd = conf['ProxyCommand'].split(' ')
            if pcmd[0].endswith('ssh'):
                ssh_cmd += ' -o ProxyCommand="{} {}"'.format(self.prog, ' '.join(pcmd[1:]))

        return ssh_cmd, target, post, conf

    def _err(self, msg):
        error("error: %s" % msg)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=SUMMARY, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-F', '--ssh-config', default=Sshconf.CONFPATH_DEFAULT, help=argparse.SUPPRESS)
    parser.add_argument('-W', '--ssh-port-fw', help=argparse.SUPPRESS)
    parser.add_argument('-J', '--ssh-jump-host', help=argparse.SUPPRESS)
    parser.add_argument('--ocsh-verbose', action='store_const', dest="loglevel", const=logging.DEBUG, default=logging.INFO, help="enable debug messages")
    parser.add_argument('--ocsh-pretend', action='store_true', help="do not actually perform the connection")
    parser.add_argument('--ocsh-examples', action='store_true', help="show example ocsh configuration and commands")
    parser.add_argument('--ocsh-install-autocompletion', action='store_true', help="install bash autocompletion for the current user")
    parser.add_argument('destination', nargs='?', help='host[action] or regex for multiple hosts')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='any OpenSSH options or remote command')
    args, ssh_options = parser.parse_known_args()

    if args.ocsh_examples:
        print("ocsh examples:\n\n"+EXAMPLES)
        exit()

    # XXX TODO create a custom parser that would pass ssh-* arguments more smoothly. Need our parser to know all SSH arguments.
    ssh_args = ' '.join(args.args)
    if args.ssh_port_fw:
        ssh_args += "-W {}".format(args.ssh_port_fw)

    if args.ocsh_install_autocompletion:
        Octossh.install_bash_completion()
        sys.exit(0)

    if not args.destination:
        parser.print_usage()
        sys.exit(0)

    logging.basicConfig(level=args.loglevel, format='ocsh: %(message)s')

    c = Sshconf(Path(args.ssh_config))

    destinations = list()
    if '*' in args.destination:
        for h in c.hosts:
            if re.match(args.destination, h):
                destinations.append(h)
    else:
        destinations.append(args.destination)
    for dest in destinations:
        if len(destinations) > 1:
            print("[+] target : %s" % dest)
        o = Octossh(c, dest, args.ssh_jump_host, ssh_args, ssh_options)
        if not args.ocsh_pretend:
            o.run()

if __name__ == "__main__":
    sys.exit(main())
