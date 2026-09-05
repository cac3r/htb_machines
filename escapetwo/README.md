## EscapeTwo

### Info:
- Name: **EscapeTwo**
- OS: **Windows**
- Type: **Assumed Compromise**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
### Brief
##### Pivot => `sa`: Leaked credentials on SMB share file `sharedStrings.xml`
Starting the Assumed Compromise test on DC01.sequel.htb using the given credentials for User `rose`. After network/host reconaissance, authenticated to the exposed SMB service, find READ access to `Accounting Department` share. Reading it's content find and unzip a `accounts.xlsx` file, which contains `xl/sharedStrings.xml` file, leaking 4 sets of credentials for Domain users, 2 of them ending up being valid (`sa` and `oscar`). 
##### Shell as `sql_svc`: MSSQL `xp_cmdshell` RCE => revshell
`sa` credential is used to authenticate via MSSQL and with a `dbo`/`sysadmin` session, enable `xp_cmdshell` for RCE to call a reverse shell to the attacker system, now having a PowerShell shell as the account running the MSSQL service, `sql_svc`. 
##### Pivot => `ryan`: Leaked password in conf. file `sql-configuration.ini`
Navigating the `C` disk find a configuration file (`C:\SQL2019\ExpressAdv_ENU\sql-configuration.ini`) that leaks another password, sprayed to all domain users end up being matched for `sql_svc` account and reused for User `ryan`. 
##### Pivot: `ryan` => `WriteOwner` => `ca_svc`: Own, Full control, Shadow credentials
Enumerating domain information like ACL and other permissions with BloodHound discover `ryan` holding `WriteOwner` over `ca_svc`. Abuse this granting ownership and full control over `ca_svc`, now able to write over `msDS-KeyCredentialLink` attribute on `ca_svc` account and abuse it using shadow credentials technique to write a generated public key to the attribute and using the other generated pair, private key, to sign a chanllenge as `ca_svc` that KDC accepts against the written public key, succesfully authenticating via kerberos passwordless login PKINIT, capturing the TGT and with it the `ca_svc` account NT Hash. 
##### Privilege Escalation => `administrator`: ESC4 - Full controll and enrollment permissions over Client Auth template, downgrade to ESC1
With BloodHound analysis and depper enumeration of ADCS as `ca_svc` with certipy, find this account has enrollment rights and Full Control over a certificate template `DunderMifflinAuthentication` for Client Authentication. This permission is abused by reconfiguring the template to accept requester supplied subject (UPN), making it ESC1 vulnerable. Now as a ECS1 template  using `ca_svc` enrollment rights to request a certificate supplying `administrator` as subject/UPN to the CSR. This `administrator` certificate is used to authenticate to the domain and retrieve the NT Hash for `administrator` account. At this point the attacker has administrator / DA privileges inside the Domain.

---
### Techniques:
- MSSQL RCE => Reverse Shell
- WriteOwner over User Abuse - Shadow Credentials
- ESC4, write permission over template Abuse - Downgrade to ESC1 vulnerable
- ESC1 vulnerable template Abuse - Supply administrator UPN in CSR => privileged cert
