## octossh - SSH password log-in and command automator

octossh automates SSH password login and command execution through annotations on `ssh_config(5)` Hosts:
* password authentication, reading password from pass[1]:
  * config:  `# ocsh pass <pass-name>`
  * command: `$ ocsh host`
* post-login command execution:
  * config:  `# ocsh post <action> "<cmd>"`
  * command: `$ ocsh host[action]`
* post-login command execution, reading additional password from pass[1]:
  * config:  `# ocsh postpass <action> "<cmd>" <pass-name>`
  * command: `$ ocsh host[action]`

[1] https://www.passwordstore.org/

Compatibility with OpenSSH is kept as much as possible:
* support usual SSH aliases, keys and command-line options
* compatible with rsync, scp and other tools using SSH for transport, see example commands
* autocompletion can be set-up with --ocsh-install-autocompletion

## Usage
```
usage: ocsh.py [-h] [--ocsh-verbose] [--ocsh-pretend] [--ocsh-examples]
               [--ocsh-install-autocompletion]
               [destination] ...

octossh - SSH password log-in and command automator

positional arguments:
  destination           host[action]
  args                  any OpenSSH options or remote command

options:
  -h, --help            show this help message and exit
  --ocsh-verbose        enable debug messages
  --ocsh-pretend        do not actually perform the connection
  --ocsh-examples       show example octossh configuration and commands
  --ocsh-install-autocompletion
                        install bash autocompletion for the current user
```

## Installation

```
pip install octossh
```

## Examples of usage
```
# connect to SSH alias 'host1' with automated password login
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

# run rsync through octossh from host1 with automated password login
rsync -e "ocsh" -avP host1:/etc/hosts /tmp/

# run scp through octossh from host1 with automated password login
scp -S "ocsh" host1:/etc/hosts /tmp/
```

## See also

* netmiko - python library to SSH to various network devices
  https://github.com/ktbyers/netmiko
* sshpass - automate SSH password-based log-in
  https://github.com/kevinburke/sshpass
* passh - sshpass alternative to automate SSH password-based log-in
  https://github.com/clarkwang/passh
