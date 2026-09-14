### Info:
- Name: **Union**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Medium**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/union/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/union/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/union/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Foothold: SQLi in `player` parameter reflecting query results
Starting the test against the target system `union` unauthenticated. After network/host reconnaissance, enumerating the exposed HTTP web service on port 80 observe a functionality to check "player" names. After probing the `player` parameter discover SQLi using UNION queries and specifying one column (null) the result from the query is reflected in the response message. With this controlled reflection enumerate database type (MySQL) and version (8.0.27), schema name (`november`), tables (`flag`), columns (`one`) and dump to obtain a flag (`UHC{F1rst_5tep_2_Qualify}`). 
###### "Granted SSH access" after valid flag submission
This flag is submitted on `challenge.php` and being valid redirects to `firewall.php`, greeted by a message stating my IP has been granted SSH access. 
#### Pivot to `uhc`: Database credential in `config.php` file -> reused for system account
Fuzzing the web application files and directories discover a `config.php`. Back to the SQL injection point, using LOAD_FILE to read system files, specify the default webroot for Debian/Ubuntu systems to list the `config.php` file `/var/www/html/config.php`. This file contains the credential for a database user `uhc` and turns out to be reused for a system account `uhc` (same identity). With this credentials connect to the target system via SSH as it exposed after passing through `firewall.php`, here obtain user.txt flag.
#### Pivot to `www-data`: `firewall.php` code flaw -> OS cmd injection
Using this access via SSH to download and inspect the PHP source code and find a code flaw in `firewall.php`, concatenating an IP served in the request by a user controlled HTTP Header `X-FORWARDED-FOR` and executed by `system()`. Abused by requesting `firewall.php` injecting OS command in added header `X-FORWARDED-FOR` (payload: `1.1.1.1; <COMMAND>;#`) and directing output to specified attacker system IP and port with NetCat. After comfirming RCE as `www-data`, inject a simple bash reverse shell payload to establish a connection to the attacker system listener.
#### Privilege Escalation -> `root`: Excessive sudo privileges on `www-data`
Connected to a shell as `www-data` enumerate sudo privileges and note very elevated privileges as this account can run all commands as any user in the system, including root. Although there are faster and better ways to acomplish the same goal (session/shell as `root`), this is abused by Setting UID to `/bin/bash` binary and executing a privileged bash session as root, here obtain root.txt final flag.  

---
---
### Techniques:
- SQLi with UNION and **reflected data** in response
- Reading system files via SQLi (concept and MySQL example)
- OS command injection over HTTP header fed as variable to a script's system execution sink
- Abusing `(ALL) NOPASSWD: ALL` sudo privilege

---
---
### Lesson:
#### SQLi with UNION and **reflected data** in response

Don't only hunt errors/conditions; **send a recognizable-output payload (`@@version`) and scan the ENTIRE response for the result.** Reflected-data is the channel that makes UNION _visible_; missing it makes you think a visible injection is blind. The output may appear in an unexpected slot (a greeting, a name field, a header), scan everything.

*Note: **`select *`** at the end worked because `flag` happened to fit the display, but `*` is risky when column counts don't match the display slot. Naming the column (`select one from flag`, since you'd found the column was `one`) would've been the disciplined move. Minor, and it worked, but worth noting you reverted to `*` under momentum.*

---
#### Reading system files (web app source code) via SQLi

This is a **standard, high-value move**, and you should internalize it as a reflex. Once you have a SQLi that can read files (`LOAD_FILE` on MySQL, given `FILE` privilege), reading the app's own source is one of the most productive things you can do, because source code hands you:

- **Database credentials**
- **Other secrets** — API keys, session secrets, hardcoded passwords.
- **The app's logic** — how auth works, where other injection/upload points are, how to reach admin functions.
- **File paths** — where uploads go, where other includes live.

**Whenever SQLi gives you file-read, reading the web source (config files especially) is a common and smart step.** `config.php`, `wp-config.php`, `.env`, `settings.py`, `database.yml` — the config file of whatever stack is running is the prime target because it _has_ to contain the DB credentials (the app needs them to connect). You reasoned to exactly the right file.

---
##### Ways to find the webroot without RCE

**1. Read the web server config (most reliable).** You have file-read — use it to read the _server's own config_, which literally states the webroot. Fixed, known paths:

- **nginx:**
`/etc/nginx/nginx.conf`
`/etc/nginx/sites-enabled/default` 

- **Apache:** 
`/etc/apache2/sites-enabled/000-default.conf` (Debian) `/etc/httpd/conf/httpd.conf` (RHEL) → the **`DocumentRoot`** directive.

This is the _best_ method because the config _tells you the answer_ rather than you guessing. You already have the primitive to do it. (This is the "follow the config" habit from your Apache/nginx work — same reflex.)

**2. Read `/etc/passwd` to infer user home/webroots.** `/etc/passwd` is always at a fixed path and readable, so it _confirms file-read works_ AND hints at webroots:

- A `www-data` or `apache` user's home might point at the web dir.
- User accounts (`/home/<user>`) suggest `/home/<user>/public_html/` or similar for user-served sites.

(This is also your "confirm file-read works at a known path" step from last message — it does double duty.)

**3. Read process/self info (Linux proc filesystem).** These pseudo-files expose runtime info at fixed paths:

- `/proc/self/environ` — environment variables of the reading process; sometimes contains `DOCUMENT_ROOT`, `SCRIPT_FILENAME`, `PWD`.
- `/proc/self/cwd/` — the current working directory (often the webroot for the web process).
- `/proc/self/cmdline` — how the process was launched, sometimes with paths.

When it works, `DOCUMENT_ROOT=` is right there.

**4. Try the common defaults (the guess you already made).** Fast to test, and often right:

- `/var/www/html/` (Debian/Ubuntu default — what you used)
- `/var/www/`
- `/usr/share/nginx/html/` (some nginx installs)
- `/srv/www/`, `/srv/http/`
- `/home/<user>/public_html/`
- Windows: `C:\inetpub\wwwroot\`, `C:\xampp\htdocs\`

Guessing is fine _as a first quick try_ (you got lucky, it held), but the point of methods 1-4 is what you fall back to when the guess returns empty — so you don't misread "wrong path" as "file-read broken."

---
#### System command injection over HTTP header fed as variable to a script's system execution sink

Headers like `X-Forwarded-For`, `X-Real-IP`, `Referer`, `User-Agent`, `X-Client-IP` are all **client-controlled and must never be trusted** as identity or fed into sensitive sinks. When you read source and see `$_SERVER['HTTP_*']` flowing into `system()`/`exec()`/SQL/`eval()`, that's an injection point — because the client controls those header values.

**Command injection via `system()` with user input.** Any time source shows `system()`, `exec()`, `shell_exec()`, `passthru()`, `popen()`, backticks, etc. with _any_ user-influenced data concatenated in, suspect command injection. It's OWASP Top 10 (Injection) and appears frequently. So "user input reaches a shell-command sink" is a _very_ common pattern — you should reflexively grep source for those functions.

**Command injection via a _header_ specifically — moderately common, and a great lesson.** Injection through headers (rather than obvious form fields) is less obvious, which is _why_ it's a real-world blind spot: developers validate form inputs but forget headers are equally attacker-controlled. `X-Forwarded-For` into a command/query is a known pattern (your box list even had "HTTP Header Command Injection - X-FORWARDED-FOR" on another IP). So: common enough to _always check headers as injection vectors_, especially when source shows a header value reaching a sink.

---
#### Abusing `(ALL) NOPASSWD: ALL` sudo privilege

With `(ALL) NOPASSWD: ALL`, the simplest and most reliable move is:

```
sudo su -
```

```
sudo -i
```

```
sudo bash
```

`sudo` is _already_ authorized to run anything as root with no password, so you just run a shell through it. Done. This is faster and cleaner than the SUID route — one command, no side effects.

##### Why the SUID route is unnecessary here (and a bit worse)

Your plan — `sudo chmod +s /bin/bash` then `bash -p` — **works**, but it's the roundabout way, and it's the method you'd use when you _don't_ have `(ALL) NOPASSWD: ALL`. Compare:

- **SUID route:** `sudo chmod u+s /bin/bash` (make bash SUID-root), then `/bin/bash -p` (run bash preserving the SUID → effective root). Two steps, _and_ it **modifies the system** — you've left a SUID-root `/bin/bash` on disk, which is a persistent, noisy artifact (a real red flag in a real engagement, and technically a new vulnerability you introduced).
- **Direct route:** `sudo su -`. One step, no system modification, no artifact.

Since `sudo ALL` lets you run `su`/`bash` as root _directly_, there's no reason to go through SUID. The SUID trick is for when your sudo/access is _narrower_ — e.g., you can only run `chmod` as root but not a shell directly. Here you can run _anything_, so run the shell.

---
---
***NOTE: (I use `Claude Opus 4.8` post testing to fill gaps and squeeze more out of each test, mostly for Lesson, responses come from debating with it and selecting what to internalize)***

---
##### Takeaway

- Watch for **reflected data** on responses when doing SQLi probes
- Avoid using `*` in UNION queries since it expands to the table's full column count (rarely matching the required number by original query).
- Have SQLi -> Try to read system files (also try write)
- Be more curious on source code and internal scripts. They may hide an abusable flaw
- HTTP headers are user controlled input, potential injection point
- `(ALL) NOPASSWD: ALL` ->  `sudo -i` / `sudo su -` directly. Don't overcomplicate with the SUID trick
