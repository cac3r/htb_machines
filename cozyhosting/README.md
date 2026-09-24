### Info:
- Name: **CozyHosting**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/cozyhosting/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/cozyhosting/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/cozyhosting/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Initial access: Session Highjack after reading `actuator/sessions`. Access to `/admin` dashboard
Starting the test against the target system `cozyhosting` unauthenticated. After network/host reconnaissance, enumerating the website exposed at port 80 HTTP discover `/error` page. Searching the error message come to know this page is the default page set by Spring Boot Java framework. Fuzzing the web using a targeted wordlist for the fingerprinted framework (included in SecLists) to discover actuator funtions like `actuator/sessions` which contains a valid session/cookie for the user `kanderson`. This cookie is used to highjack the session and access the `/admin` dashboard. 
#### System foothold: OS command injection in `/executessh` leading to RCE and shell as `app`
In this dashboard find a functionality to include hosts (`/executessh`). This function uses the user controlled values from  `host` and `username` to conform and execute a command with ssh. The `username` parameter is injectable but the backend filters spaces (` `). Adding a separator (`;`) to append a new command and using brace expansion syntax (`{a,b}`) to bypass the filter allows to execute arbitrary commands. Base64 encoding a reverse shell payload and, with the prior syntax mentioned, conform the final payload (URL encoded). Executing it decodes the base64 and runs the reverse shell payload, obtaining a shell as user `app`. 
#### Pivot to `postgres` db user: Reading Spring Boot configuration files - `application.properties`
Listing the contents of the directory `/app` (where shell landed) find the source code JAR file (`cloudhosting-0.0.1.jar`), send it to attacker system via SSH. After unzip, searching for files containing configuration (`*.properties`) find `application.properties` (inside `BOOT-INF/classes/`) which contains database (PostgreSQL) configuration and the database user credential `postgres:Vg&nvzAQ7XxR`.
#### Credential harvest: Dump PostreSQL database `users` table
Enumerate the database with the obtained credential and dump the contents of `users` table, saving hashes (bcrypt) for `kanderson` and `admin`. The `admin` hash turns out cracked, plaintext credential `manchesterunited`. 
##### Pivot to `josh`: Password reuse
This credential is checked against system user `josh` and results to be valid, the password is reused. Switch to a session as `josh` and read the user flag (`user.txt`).
#### Privilege escalation: Execute ssh (`ProxyCommand`) as root 
Enumerating sudo privileges, find `josh` is permitted to execute `/usr/bin/ssh` as `root`. Abuse this by executing ssh with sudo, setting `ProxyCommand` to `/bin/sh`, obtaining a shell as root, capturing the final flag (`root.txt`).

---
---
### Techniques:
- Fingerprint app via default error page
- Session hijack (leaked though Spring Boot `actuator/sessions`)
- OS command injection with space filtering
- Read Spring Boot configuration files
- Enumerate PostgreSQL database authenticated
- Abuse SSH sudo privilege - Read files as root / Shell as root
---
---
### Lesson:
#### Spring Boot

##### Default error page:

![[06 4.png]]

Whitelabel Error Page = Spring Boot

##### Fuzz for known endpoints with SecLists wordlist:

```
SecLists/Discovery/Web-Content/Programming-Language-Specific/Java-Spring-Boot.txt
```

Interesting to access:

`actuator/sessions`  --> Sessions --> Potential Session Hijack
`actuator/env`
...

##### Once access to system, source code:

Get the .jar on disk, unzip

Find the interesting properties/config files

```
find . -name *.properties
```

Examples:

`./BOOT-INF/classes/application.properties`
`./META-INF/maven/htb.cloudhosting/cloudhosting/pom.properties`

---
#### OS command injection with space filtering

The user input `host` and `username` is used on a system command (In this case with ssh).
The backend is filtering spaces, using brace expansion to omit spaces and to expand content after filter.

For the reverse shell, the command is full of spaces, so base 64 encoding it solves this, plus evades other pontential filters.

```
;{echo,<b64>}|{base64,-d}|bash;
```

"echo the space free b64 encoded shell → decode it back to the real command → execute"

The full payload is then URL encoded to evade HTTP level problems with syntax.


*(Claude Opus 4.8 advise below)*
##### Space-substitutes worth adding to your notes

Since the filter here was spaces, here are the standard space-free tricks (all worth knowing — filters vary):

- **`{cmd,arg}`** — brace expansion (what you used).
- **`${IFS}`** — the IFS variable _is_ whitespace, so `sleep${IFS}3` = `sleep 3`. Extremely common.
- **`$IFS$9`** or **`${IFS%??}`** — variants when `${IFS}` alone gets mangled.
- **Tabs** instead of spaces sometimes pass.

---
#### Enumerate PostgreSQL database authenticated

Connect to db with psql

```
psql -h <host> -U <user>
```

List databases

```
\list
```

Use `<database>`

```
\c <database>
```

List tables inside it

```
\d
```

Dump contents normally

```
select * from <table>;
```

---
#### Abuse SSH sudo privilege

https://gtfobins.org/gtfobins/ssh/
##### Reading files as root (example `root.txt`)

```
sudo ssh -F /root/root.txt x
```

 `-F` tells ssh to use the specified file as its configuration file instead of the default. ssh reads and parses that file expecting SSH config.

To abuse point `-F` at a file you want to read (`/root/root.txt`), a file you cant normally read, but ssh runs as root so it can. ssh tries to parse `/root/root.txt` as a config file. Since the flag contents are not valid SSH config syntax, ssh errors, and the error message prints the content.
##### Shell as root

```
sudo ssh -o ProxyCommand=';/bin/sh 0<&2 1>&2' x
```

`ProxyCommand` is a SSH feature for connecting through a proxy/jump host. Instead of connecting directly, ssh **runs a command** and uses that command's input/output as the connection to the server. Its meant for things like `ProxyCommand=nc %h %p` (pipe through netcat) or tunneling through a bastion.

To abuse set `ProxyCommand` to `/bin/sh` so instead of proxying, ssh runs `/bin/sh` as root, giving you a root shell.

```
;/bin/sh 0<&2 1>&2
```

- `;` - separator.
- `/bin/sh` - spawn a shell (as root, since ssh runs as root).
- `0<&2` - redirect stdin from stderr.
- `1>&2` - redirect stdout to stderr.

---
#### Takeaway
- Research error pages and messages, specially odd ones
- Fuzz with targeted tech/framework wordlists when possible
- Spring Boot error page, actuators and configuration/properties
- OS command injection space filtering bypass with brace expansion
- PostgreSQL (psql) command line syntax to enumerate database
- Abuse of permision to run SSH (ssh) as root
