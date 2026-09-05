## TheFrizz

### Info:
- Name: **TheFrizz**
- OS: **Windows**
- Type: **Unauthenticated**
- Difficulty: **Medium**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/TheFrizz/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/TheFrizz/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/TheFrizz/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
### Brief:
##### Foothold: HTTP - Gibbon framework exploit - CVE-2023-45878
Starting the test unauthenticated. After network/host reconnaissance, enumerating HTTP service, discover a website using Gibbon framework version 25.0.0. Looking up this technology version in www.cvedetails.com find various CVEs, pick and use CVE-2023-45878 (which affects versions below 25.0.1) to abuse the rights to write over a PHP file in the server, enabling to inject malicious PHP code to achieve RCE calling a GET to the writen file from browser, all this automated by a script https://raw.githubusercontent.com/davidzzo23/CVE-2023-45878/refs/heads/main/CVE-2023-45878.py. 
This RCE is used to obtain a reverse shell, now with a PowerShell shell as the account running the web service `w.webservice`.
##### Pivot -> `MrGibbonsDB`: SQL database user leaked credentials in config file
Navigating and listing the contents of the web server directory, find a `config.php` file leaking a credential for the user for the SQL Database `MrGibbonsDB`.
##### Pivot -> `f.frizzle`: Extraction of user Hash in DB table `gibbonperson`
Now connected to the database `Gibbon` list tables and query for `gibbonperson` table, then to query for sensitive columns `username`, `passwordStrong`, `passwordStrongSalt`. Showing contents of this columns find one row containing the values for `f.frizzle`. This password hash and salt is formed to a hash in a file fed to hashcat to crack with mode 1420 (sha256, salt:pass), retrieving the plaintext password for User `f.frizzle`.
##### Remote access as `f.frizzle`: SSH via kerberos auth (failed)
With SSH service exposed and `f.frizzle` being a member of Remote Management Users, using the credential to request a kerberos TGT since the target domain disables NTLM authentication. Passing this TGT with ssh -K to connect to the target machine encounter resolution and KDC, DNS errors, preventing connection, and therefore halting further progress after a significant amount of debugging, finishing the test at this point.

*Post testing, the cause of errors is debated and noted. Coming to the conclusion that the attacker missed to include the target DC in the attacker system resolution and FQDN/realms in kerberos config files. Leaving test open to future attempts.*

---
### Techniques:
- CVE-2023-45878 for Gibbon framework < 20.0.1 exploitation
- Database enumeration with mysql.exe via PowerShell
- SSH with kerberos

---
---
### Lesson:
#### Internal DB enumeration
- When you have a shell on a box and find database credentials, you need _some_ way to talk to the database. You have two options — connect _remotely_ from your attack machine, or connect _locally_ from the shell you already have (LotL style). And frequently the database is **only listening on localhost** (bound to 127.0.0.1), not exposed to the network — which is actually good security practice.

Common client binaries:
- **MySQL / MariaDB** (`mysql` / `mysql.exe`) — extremely common, because it's the default database behind a huge fraction of web apps (the "M" in LAMP/WAMP stacks). Gibbon, WordPress, most PHP apps → MySQL. You'll see this a lot.
- **MSSQL (Microsoft SQL Server)** — _the_ one to know for AD/Windows environments, and arguably more OSCP-relevant than MySQL for the AD side. Client tools: `sqlcmd`, or you connect with impacket's `mssqlclient.py`. MSSQL is huge because `xp_cmdshell` (saw on [EscapeTwo](https://github.com/cac3r/htb_machines/tree/main/escapetwo)) turns DB access into RCE. On Windows/AD boxes, MSSQL is often the star.
- **PostgreSQL** (`psql`) — common with newer/Linux web apps.
- **SQLite** — file-based, no server; you just read the `.db`/`.sqlite` file directly (sometimes with the `sqlite3` binary). Common in smaller apps.

---
#### Hashcat

- `--username`: Used when a hash starts with a username identifier. Without it, hashcat thinks the username part is part of the hash to crack. It's a _parsing_ instruction for hashcat when it reads your file to crack. Alternatively you could just _not_ put the username in the file at all.

Hash - Salt order:

**The order your fields appear in your _file_ (`hash:salt`) has NOTHING to do with which mode is correct**. You can store the hash different ways, but the important thing is to match how the hash was originally created. 
- Either `hash:salt`, or `salt:hash`. It depends on the code that created it.

**So how to know what is the correct order and mode out of the different possibilities hashcat may print after running identification?**
- If you know the framework/technology/source of code. **Search on internet**:       "<tech/framework> password hash algorithm".
- Or just try each mode that hashcat listed, till any works.
- Alternatively, having access to the source code, could analyze and find the logic that creates the hash, appending order and algorithim.

---
#### SSH and Kerberos quirk

- **System/GSSAPI tools (`ssh -K`, `kinit`, `smbclient -k`, some others): DO need krb5.conf.** These use the operating system's _native_ Kerberos library, which reads `/etc/krb5.conf` to find the KDC. `ssh -K` is squarely in this camp — that's why it, specifically, threw "cannot find KDC" while impacket sailed through. So it's **not** "always for Kerberos" — it's "for the _system_ Kerberos tools," and `ssh -K` happens to be one.

**First**: Add target DC to `/etc/resolv.conf` temporarily during test. Point DNS at the DC:

```
# /etc/resolv.conf
nameserver <DC_IP>
```

**Second**: Edit `/etc/krb5.conf`:

Example for domain: `frizz.htb`, hostname: `frizzdc`

```
[libdefaults]
    default_realm = FRIZZ.HTB
    dns_lookup_kdc = false
    dns_lookup_realm = false

[realms]
    FRIZZ.HTB = {
        kdc = frizzdc.frizz.htb
        admin_server = frizzdc.frizz.htb
    }

[domain_realm]
    .frizz.htb = FRIZZ.HTB
    frizz.htb = FRIZZ.HTB
```

OR easier

Create it with NetExec and copy it to `krb5.conf`

```
nxc smb <FQDN> --generate-krb5-file <file>.krb
```

Add it to `krb5.conf`

```
sudo cp <file>.krb /etc/krb5.conf
```

And of course make sure to be in sync with target system clock. (ntpdate)

---

The important takeaway preparing for OSCP+:
- **The web → RCE → config → database → credential-reuse chain IS the OSCP web-to-foothold pattern.** This is the most transferable thing on the box. Public app → find the version → look up the CVE → get code execution → _loot the config files_ → find database/service creds → reuse them to pivot. That exact shape — especially "web shell, then hunt `config.php`/config files for credentials" — recurs constantly on the exam. The specific CVE (2023-45878) is disposable; the _habit_ of "I have a shell, now I ransack config files for creds" is core. Bank that loop. - (Claude Opus 4.8)
