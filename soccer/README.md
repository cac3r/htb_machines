### Info:
- Name: **Soccer**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/<>/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/<>/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/<>/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
### Brief:
##### Foothold: File Upload exploit on Tiny File Manager 2.4.3 using it's default credentials
Starting the test against target system `soccer` unauthenticated. After network/host reconnaissance, probing the exposed HTTP web service on port 80, discover (by fuzzing) a `tiny/` directory, redirecting to a login page for `Tiny File Manager`. Viewing the source code note a link for the official repo of this technology and also the specific version (2.4.3). Searching for the fingerprinted technology discover a common exploit for versions before or equal 2.4.6, applying for target 2.4.3. This exploit consist of a path traversal vulnerability that enables authenticated users to upload PHP files for RCE. To obtain the credential for authentication, read the official documentation on GitHub, which specifies the default admin credentials used for first setup (`admin:admin@123`). Now with authentication exploiting the mentioned vulnerability uploading a malicious PHP file to `/tiny/uploads` achieving RCE and with a basic bash payload, a reverse shell as the account running the backend `www-data`. 
##### Asset Pivot: Reading `nginx` config -> New subdomain
Now connected with a interactive shell to the target machine read the `nginx` configuration files. `/etc/nginx/sites-enabled/soc-player.htb` includes configuration for subdomain `soc-player.soccer.htb`, added subdomain to local `/etc/hosts` to continue probing there.
##### User Pivot: SQLi on `id` JSON parameter in ticket validation functionality 
Navigating this new subdomain website, register and login to be redirected to `check/`, a function sending football match tickets IDs in a JSON format to a websocket backend on port 9091 checking against the web database and responding whether the ticket is valid or not. Since is a user controlled value feeding ,what it seems, a database lookup, checking for SQLi with automated tool `sqlmap` which discovers Blind boolean-based and Blind time-based injection on the mentioned data form, enabling to enumerate databases (`soccer_db`), tables (`accounts`) and finally dumping contents, retrieving a new credential set for user `player` (`player:PlayerOftheMatch2022`). The password is reused for the system user account `player`, connecting via SSH successfully and capturing `user.txt` flag.
##### Privilege Escalation: Abusing `dstat` plugin feature + `doas` execution as root
Once in this shell as `player` via SSH, enumerate SUID binaries to discover `doas` presence. Reading its configuration `doas.conf` note the permission for the controlled user `player` to execute `dstat` as root. `dstat` is a known tool used for system information and stats. On its official manual, is explicit that anyone can create and use their own `dstat` plugins. Having write access to a commonly used system directory for this plugins can plant a malicious plugin to then run it with `dstat` as root (with `doas`), therefore enabling arbitrary code execution as root. Creating the plugin file with name pattern `dstat_<NAME>.py` and writing a oneline python script to spawn `/bin/bash` in the writable `/usr/local/share/dstat`. Executing it with `doas`, spawning a shell as root and finishing capturing `root.txt` flag.

---
### Techniques:
- Exploiting known File upload vulnerability on discovered technology `Tiny File Manager 2.4.3`
- Reading `nginx` server configuration files
- Enumerating and dumping SQL database with automated tool `sqlmap`. Due to time-based SQLi in JSON field `id` parameter. 
- Enumerating SetUID binaries
- Enumerating `doas` permissions (similar to `sudo`)
- Abusing `/usr/bin/dstat` (system info tool) execution permission as root by creating a malicious plugin spawning `/bin/bash`, shell as root.

---
### Lesson:
##### Lookup target technology/framework and read official documentation

The documentation can have valuable information (like default credentials).

---
##### Read `nginx` server configuration files

Once having a shell or read access as a user with permission for it, read server configuration files. 
For `nginx` check: `sites-enabled/` directory

In this case, leaked a subdomain.

```
/etc/nginx/
├── nginx.conf................Main config
├── sites-available/..........ALL defined server blocks (vhosts)
├── sites-enabled/............symlinks to the active ones
├── conf.d/...................Additional config, often *.conf       |                             auto-included
├── snippets/.................Reusable fragments (ssl params,      |                             fastcgi, etc.)
└── modules-enabled/..........loaded modules
```

Same idea as Apache. `sites-enabled` holds what's actually live,.
Always also check `conf.d/` and `nginx.conf`.

---
##### Using `sqlmap` against potential SQLi

In this case, against a parameter in a POST request sent to a websocket talking to the database to check valid ticket IDs sent in JSON format.

Running automated SQLi probe with `sqlmap`

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3
```

- `-u` target URL
- `--data` to specify the parameter, field for payload (URL encoded, JSON, XML, ...)
- `-dbms` to specify database type
- `--batch` for no interaction (automatic yes responses)
- `--level` (1-5) the level of variation of injections
- `--risk` (1-3) how dangerous can it get (3, all payloads, but noisy, hammering fine for labs)

If it identifies any injection type will show in the output, type of injection and used payload.

After confirming a possible injection:

Enumerating databases (`--dbs`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 --dbs
```

Will show databases

Enumerating tables (`-D <db> --tables`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 -D soccer_db --tables
```

Will show tables

Listing contents in table (`-T <table> --dump`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 -D soccer_db -T accounts --dump
```

Will dump all information inside a table

*Note on finding SQLi:`{"id": "1234"}`. An `id` with a numeric value screams "this gets used in a query like `SELECT ... WHERE id = 1234`." Parameters named `id`, `user`, `search`, `q`, `category`, `order`, `sort`, `filter`, `page` anything that plausibly maps to a row lookup are prime suspects. The name and value shape hint at what the backend does with it.*

*`sqlmap` is only permitted for one machine in OSCP exam*

---
##### Enumerating SUID binaries

**SUID (Set User ID).** "when anyone runs this program, it runs with the privileges of the file's owner, not the privileges of the user who launched it."

Find SUID binaries

```
find / -perm -4000 2>/dev/null
```

- **`-perm`**  "match by permission bits"
- **`-4000`** the permission you're matching. Linux permissions are octal: the SUID bit is `4000` (the `4` in the leading "special" position, `2000` would be SGID.
- **`2>/dev/null`** Searching the whole filesystem as a normal user hits tons of "Permission denied" errors on directories you can't read, hide that noise so you only see the actual results.

`-` in `-4000` matters: it means "at least these bits are set" rather than "exactly these bits."
`-perm -4000` = "any file that has the SUID bit set, regardless of its other permission bits."

In plain English: Find every file, anywhere, that has the SUID bit set, and don't clutter the output with permission errors.

Most entries are standard, expected SUID binaries (`passwd`, `sudo`, `mount`, `su`, `ping`, ...) they're supposed to be there. The thing is to spot:

1. Anything non-standard / custom.  A binary that isn't part of a normal install, especially in odd locations (`/opt`, `/home`, `/tmp`).
2. Standard binaries with known abuses. Lookup GTFOBins.

To see owner and permissions in the output

```
find / -perm -4000 -type f -exec ls -la {} \; 2>/dev/null
```

`ls -la` shows the `-rwsr-xr-x`, that `s` in the owner's execute slot is the visual marker of the SUID bit.

SGID is the sibling bit (`-perm -2000`) that does the same thing for the file's _group_ instead of owner. Worth searching too.

```
find / -perm -2000 2>/dev/null
```

---
##### Enumerating `doas` permissions

`doas` is an alternative for `sudo` typically found on OpenBSD operating systems, but that can be installed on Debian-base Linux OSes like Ubuntu.

It lets a permitted user run a command as another user (usually root), exactly like `sudo`. Same job: "run this one command as root without needing a session as root."

Find doas.conf

```
find / -name doas.conf 2>/dev/null
```

The config normally lives at:
```
/etc/doas.conf         
/usr/local/etc/doas.conf
```

List contents. It will output any permission to run executables as root.

As with sudo, rules can match by username or by group. A group rule (marked with a `:`) applies to every member of that group:

```
permit :devs as root
```

"anyone in the `devs` group may run anything as root." Permissions are the union of rules matching your username and any group you belong to.

*Note: It comes from the OpenBSD project, written around 2015 as a deliberate reaction to `sudo`. It's not for OpenBSD only. Packaged for Linux (`opendoas` on Debian/Ubuntu/Arch...).*

*Why use it instead of sudo?*
*The one-word answer is **simplicity**. The OpenBSD folks argued most people use only a part of sudo's features, so they built a minimal alternative, a few hundred lines of code and a simple config format. Less code = fewer bugs = smaller attack surface. That's the core.*

---

##### Abusing `/usr/bin/dstat` (system info tool) execution permission as root by creating a malicious plugin spawning `/bin/bash`, shell as root.

`dstat` is a tool for getting system information.
Anyone can create their own dstat plugins.

Paths that may contain external `dstat_*.py` plugins:

```
~/.dstat/
(path of binary)/plugins/
/usr/share/dstat/
/usr/local/share/dstat/
```

Plugins are Python scripts with the name pattern `dstat_<NAME>.py`.

Creating malicious plugin to run with root executable script, which will spawn a shell (`/bin/bash`) as root.

```
import os

os.system("/bin/bash")
```

On a writable directory. Maybe `/usr/local/share/dstat

```
nano /usr/local/share/dstat/dstat_<NAME>.py
```

Run it as root  (example with `doas`)

```
doas /usr/bin/dstat --<NAME>
```

If executed a Shell as root should be spawned

----
---
###### Takeaway

What `soccer` surfaced the most, my lack of SQLi knowledge and practice. 

Takeaway points:
- Understanding **SUID binaries**, **doas** and difference/correlation with sudo privileges
- Refresh `sqlmap` syntax
- Understanding what **nginx** service configuration files to look for and compare to Apache
- Give more importance to **official documentation** on discovered technologies/frameworks
- A better understanding on how **binaries and permissions** are enumerated and exploited to escalate privileges on Linux environments

---

An additional question left unanswered:
The dumped database via SQLi only contained the `player` row. If the table `accounts` on `soccer_db` database is used to store users data, the account the attacker registered should have been listed. This makes me wonder if the database stores application data for either `soc-player.soccer.htb`,  `soccer.htb` or both, if they share same backend/database, or if is used to store credentials for other services, like system accounts. Having to drop or reclassify the "reused credential" finding, because the database credential would be stored for the system user, and not for the web application, so the vulnerability isn't reuse but storing the credential there at first place (or only point SQLi)... 

After debating with Claude Opus 4.8, came to the idea that the app's registration is cosmetic/non-persistent. On many CTF boxes, the registration exists mainly to give you a session to reach the vulnerable `check/` endpoint, it isn't necessarily meant to create durable store. 
