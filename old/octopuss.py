#!/usr/bin/env python

# == Usage ==
# op globi(root:root@10.175.6.7:22)^globa(pipeau:p@10.71.4.1:22)^globou(root:toor@192.168.1.1:2222)
# op globi^globa^globou^plop(192.168.3.1:22)
# op -plop
# op bizt(root:root@10.8.0.22)^-plop
# op bizt(root:root@10.8.0.22)^globi^-plop

# == Host Configuration file ==
# Format ? 
# [local] # always here
# globi = root:root@10.175.6.7:22
# [oam]
# testbed = kiwi@127.0.0.1
# production = kiwi@127.0.0.1
# [testbed]
# omu = kiwi@127.0.0.1
# [production]
# toto = kiwi@127.0.0.1
# == Path Configuration file == USELESS, included in hosts
# globi^globa^globou
# globi^globa^globou^plop
# bizt^globi^globa^globou^plop

# == Notes ==
# * remember connection paths
# * need to detect if a connection is successfull before remembering it
# * can remember from which ip address a connection was done (ifconfig), and then auto detect where to start connecting in the connection path

import sys
import re
import ConfigParser

def build_sshproxy(ptree, origin, perspective):
    def recursearch(ptree, origin, perspective):
        for section in ptree.sections():
            items = ptree.items(section)
            for (name, value) in items:
                if name == perspective:
                    if section == origin:
                        return [(name, value)]
                    else:
                        return recursearch(ptree, origin, section) + [(name, value)]
        return []

    path = recursearch(ptree, origin, perspective)
    if DEBUG: print "XXX build_sshproxy: path=%s" % path

    pathlen = len(path)
    remote = path[-1][1]
    if pathlen > 1:
        proxies = 'ssh %s' % (path[0][1])
        qt = pathlen-1
        for i in path[1:-1]:
            qt -= 1
            proxies = 'ssh -o ProxyCommand='+'\\'*qt+'"'+proxies+' nc '+i[1].split('@')[1]+' 22'+'\\'*qt+'" '+i[1]
        proxies = '-o ProxyCommand="%s nc %s 22"' % (proxies, remote.split('@')[1])

    if DEBUG: print "XXX build_sshproxy: proxies="+proxies
    if DEBUG: print "XXX build_sshproxy: remote="+remote

    return proxies, remote



def rexec(ssh_proxy, remote, cmd):
    if DEBUG:
        print 'ssh %s %s "%s"' % (ssh_proxy, remote, cmd)
    # ssh = subprocess.Popen(["ssh", ssh_proxy, remote, '"'+cmd+'"'])
    ssh = subprocess.Popen("ssh "+ssh_proxy+" "+remote+' "'+cmd+'"', shell=True)
    ssh.wait()
    return ssh.returncode

def rput(ssh_proxy, remote, file_name):
    if DEBUG:
        print "scp %s %s %s:%s" % (ssh_proxy, file_name, remote, NMA_DIR)
    scp = subprocess.Popen("scp %s %s %s:%s" %
                            (ssh_proxy, file_name, remote, NMA_DIR), shell=True)
    scp.wait()
    return scp.returncode

def rget(ssh_proxy, remote, file_name):
    if DEBUG:
        print "scp %s %s:%s ." % (ssh_proxy, remote, NMA_DIR+file_name)
    scp = subprocess.Popen("scp %s %s:%s ." %
                            (ssh_proxy, remote, NMA_DIR+file_name), shell=True)
    scp.wait()
    return scp.returncode

if len(sys.argv) < 2:
  print ("Usage: %s target" % (sys.argv[0]))
  sys.exit(1)

# load conf
conf_hosts = ConfigParser.SafeConfigParser()
conf_hosts.read("perspectives.txt")

targets = sys.argv[1].split('^')
ntarget = len(targets)

# build ssh proxy command
for target in targets:
    print "target: %s" % target
    spec = re.match("\w*\((.*)\)", target)
    if spec:
        print "  spec: %s" % spec.group(1)
        x = re.match("(\w*)(:\w*)?(@.*)(:\d*)?", spec.group(1))
        if x:
            print x.groups()
    # exists ?
    # append
    # if -prefix, guess from previous path

# write path 
