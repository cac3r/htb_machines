## Voleur
### Info:
- Name: **Voleur**
- OS: **Windows**
- Type: **Assumed Compromise**
- Difficulty: **Medium**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/voleur/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/voleur/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/voleur/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Recon & Enum
Starting the test against the target system `DC.voleur.htb` with given credentials for `ryan.naylor` as this is an assumed breach engagement. After host reconnaissance, validating given credential discover NTLM is disabled, forcing to use Kerberos for authentication. After configuring attacker system files (`/etc/hosts`, `/etc/krb5.conf`) and updating clock to sync with target DC in order to use Kerberos, get a ticket (TGT) for `ryan.naylor` and pass it to start authenticated enumeration by checking SMB shares. Having READ permission over `IT` share, use NetExec `spider_plus` module to download `IT` and other readable shares. Under `IT` share find `Access_Review.xlsx` file, identified as `CDFV2 Encrypted` (file encrypted by password derived key).
#### Credential harvest: Exposed sensitive file encrypted with weak password
Extracting the password hash protecting `Access_Review.xlsx` using `office2john` utility and cracking with mode `9600` + rockyou.txt password list recover the plaintext password: `football1`. Utilize this password to decrypt the file using `msoffcrypto-tool`, returning a `Microsoft Excel 2007+` file that can open with LibreOffice Calc. This file (as its filename hints) is an access review file with information about domain accounts and their permission (used by SOC 2 audits as a defensive security practice to catch and remove access people shouldn't have anymore). The file contains 10 domain accounts and their permissions, plus 3 passwords written in notes column. The passwords are checked against all domain accounts (without trouble as the domain password policy dont include lockout threshold), returning valid credentials for `svc_ldap` and `svc_iis`.
#### Pivot to privileged service account: ACE WriteSPN
Collecting domain data via LDAP using BloodHound (NetExec ingestor) analyze potential paths to escalate privileges finding `svc_ldap` has WriteSPN ACE over `svc_winrm`, which is a member of Remote Management Users. After getting a TGT for `svc_ldap` in order to authenticate via Kerberos, this ACE is abused by "Targeted Kerberoast", writing a temporary SPN to the target account, and requesting a TGS, capturing the accounts's TGS-REP hash and cracked with hashcat mode 13100 + rockyou.txt password list, recovering the plaintext password: `AFireInsidedeOzarctica980219afi`. Getting a TGT for this new controlled account `svc_winrm` can use the ticket to connect via WinRM and establish a shell as `svc_winrm` in the target system `DC.voleur.htb`. (Here obtain `user.txt` flag).

---
---
### Techniques:
- *(Overall)* Enumerating and probing a domain with NTLM disabled, using kerberos
	- Edit configuration (`/etc/krb5.conf`, `/etc/hosts`)
	- Sync clock with KDC
	- Get TGT (impacket `getTGT`)
	- Export TGT and use with tools (`-k`, `--no-pass`, etc...)
- Extracting hash from password protected Microsoft encrypted file (`.xlsx` - `CDFV2 Encrypted`) using `office2john`
- Decrypt Microsoft encrypted file (`.xlsx` - `CDFV2 Encrypted`) using `msoffcrypto-tool` for Linux
- Collecting Domain data using NetExec BloodHound ingestor feature
- Abusing ACE WriteSPN over account -> Targeted Kerberoast

---
---
### Lesson:
##### Encrypted / Password protected Microsoft Office file

Extract hash: `office2john`

```
office2john <file>
```

Example hash: `$office$*2013*` -> Mode `9600`

If encrypted and have the password: `msoffcrypto-tool` 
https://isc.sans.edu/diary/25826

```
msoffcrypto-tool <file> <output_file> -p '<pass>'
```

Then check output file type

```
file <file>
```

---
##### Modern `rusthound` alternative instead of legacy `bloodhound-python`: NetExec bloodhound ingestor

NetExec has a ingestor mode for bloodhound CE (Added in Dec 24, 2025 v.1.5.0: https://github.com/Pennyw0rth/NetExec/releases/tag/v1.5.0: 
"Make nxc compatible with bloodhound-ce zip by [@mpgn](https://github.com/mpgn) in [#664](https://github.com/Pennyw0rth/NetExec/pull/664). BloodHound Community Edition is taking over and now we also support its collector. If you want to swap to the legacy collector, change the config setting.").

Using nxc to collect data files that are compatible with BloodHound CE

```
nxc ldap <DC_IP> -u '<user>' -p '<pass>' --bloodhound --collection All -d <doamin> --dns-server <DC_IP/FQDN>
```

With kerberos auth
```
nxc ldap <DC_IP> --use-kcache --bloodhound --collection All --kdcHost <KDC/DC_FQDN> -d <doamin> --dns-server <DC_IP/FQDN>
```

---
###### `klist` for kerberos tickets on Linux

Check current tickets using `klist`:

```
klist
```

Example output:

```
Ticket cache: FILE:svc_winrm.ccache
Default principal: svc_winrm@VOLEUR.HTB

Valid starting       Expires              Service principal
11/25/2026 01:07:15  11/25/2026 11:07:15  krbtgt/VOLEUR.HTB@VOLEUR.HTB
	renew until 11/26/2026 01:07:15
11/25/2026 01:14:42  11/25/2026 11:07:15  HTTP/DC@VOLEUR.HTB
	renew until 11/26/2026 01:07:15
```
---
###### `spider_plus` from NetExec for SMB shares

`spider_plus` is a good alternative for `smbclient` specially in NTLM disabled envirenments since `smbclient` -k option is deprecated.

Download all files in readable shares (using kerberos ticket):

```
nxc smb <IP> --use-kcache -M spider_plus -o DOWNLOAD_FLAG=True
```
