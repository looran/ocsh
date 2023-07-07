class Octossh(object):
    #CONFPATH_DEFAULT = Path.home() / ".ocsh_config.yaml"
    #LOGIN_EXPECT = [
    #    "(?i)are you sure you want to continue connecting",
    #    r"[#$]",
    #    r'(?i)(?:password:)|(?:passphrase for key)',
    #    "(?i)permission denied",
    #    "(?i)terminal type",
    #    pexpect.TIMEOUT,
    #    "(?i)connection closed by remote host",
    #    pexpect.EOF
    #]
    #LOGIN_EXPECT_0_ARE_YOU_SURE = 0
    #LOGIN_EXPECT_1_SHELL = 1
    #LOGIN_EXPECT_2_PASSWORD = 2
    #LOGIN_EXPECT_3_PERMISSION_DENIED = 3
    #LOGIN_EXPECT_4_TERMINAL_TYPE = 4
    #LOGIN_EXPECT_5_TIMEOUT = 5
    #LOGIN_EXPECT_6_CONNECTION_CLOSED = 6
    #LOGIN_EXPECT_7_EOF = 7

    def run(self):
        #p.logfile_read = sys.stderr
        #if self.opts:
        #    if shutil.which('pass') is None:
        #        raise self._err("you must install 'pass', see https://www.passwordstore.org/")
        #    password = subprocess.run(["pass", self.topt['pass']], capture_output=True).stdout.decode().strip()
        #while True:
        #    ret = p.expect(self.LOGIN_EXPECT, timeout=3)
        #    info("XXX RET %s" % ret)
        #    if ret == self.LOGIN_EXPECT_1_SHELL:
        #        sys.stderr.write(p.before.decode())
        #        sys.stderr.write(p.after.decode())
        #        break
        #    elif ret == self.LOGIN_EXPECT_2_PASSWORD:
        #        sys.stderr.write(p.before.decode())
        #        sys.stderr.write(p.after.decode())
        #        p.sendline(password)
        #    elif ret == self.LOGIN_EXPECT_5_TIMEOUT:
        #        p.wait()
        #        return


    def _get_target_cmd(self, target):
            #ssh_cmd = "ocsh --ocsh-expect '[Pp]assword:' '%s'" % password
        #if 'post-pass' in conf:
        #    post_input = subprocess.run(["pass", conf['post-pass']], capture_output=True).stdout.decode().strip()
