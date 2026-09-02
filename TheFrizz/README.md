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

### Techniques:
- CVE-2023-45878 for Gibbon framework < 20.0.1 exploitation
- Database enumeration with mysql.exe via PowerShell
- SSH with kerberos

---
---
### Lesson
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

Edit /etc/krb5.conf:
**Make sure `/etc/krb5.conf` actually contains this:** 

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

Also can help: Adding target DC to `/etc/resolv.conf` temporarily during test.

```
# /etc/resolv.conf
nameserver <DC_IP>
```

---

The important takeaway preparing for OSCP+:
- **The web → RCE → config → database → credential-reuse chain IS the OSCP web-to-foothold pattern.** This is the most transferable thing on the box. Public app → find the version → look up the CVE → get code execution → _loot the config files_ → find database/service creds → reuse them to pivot. That exact shape — especially "web shell, then hunt `config.php`/config files for credentials" — recurs constantly on the exam. The specific CVE (2023-45878) is disposable; the _habit_ of "I have a shell, now I ransack config files for creds" is core. Bank that loop. - (Claude Opus 4.8)
