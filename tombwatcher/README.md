## TombWatcher

### Info:
- Name: **TombWatcher**
- OS: **Windows**
- Type: **Assumed Compromise**
- Difficulty: **Medium**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/tombwatcher/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/tombwatcher/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/tombwatcher/attack_chain.png)   - Attack chain diagram
- **`screenshots/`**           - Supporting screenshots

---
### Brief:
#### Pivoting/Domain Escalation: ACL abuse
###### `Henry` -> `WriteSPN` -> `Alfred`: Targeted Kerberoast
Starting the Assumed Compromise test on DC01.tombwatcher.htb using the given credentials for User `Henry`. After network/host reconnaissance, retrieving domain information with BloodHound, querying "Shortest path from Owned objects" (`Henry` User) discover a chain of controls over different objects that enables domain escalation. Starting with User `Henry`  `WriteSPN` right over User `Alfred`, abusing it writing a SPN to the account to apply kerberoasting (request a TGS) retrieving the user's KRB5TGS Hash, cracked to a plaintext password.

---
###### `Alfred` -> `AddSelf` -> `Infrastructure` Group: Add to group
Now with User `Alfred` controlled, abusing `AddSelf` permission over "`Infrastructure`" Group, adding `Alfred` to the group.

---
###### `Infrastructure` -> `ReadGMSAPassword` -> `ansible_dev$`: Dump gMSA
As a member of "`Infrastructure`" Group, which holds `ReadGMSAPassword` right over the gMSA `ansible_dev$`, the account's managed password is read from its `msDS-ManagedPassword` attribute, recovering `ansible_dev$` account NT hash.

---
###### `ansible_dev$` -> `ForceChangePassword` -> `sam`: Change password
With this computer account controlled, abusing `ForceChangePassword` over User `sam`, simply changing this latter user password, now controlled.

---
###### `sam` -> `WriteOwner` -> `John`: Grant Ownership, Modify DACL, Change password
`sam` `WriteOwner` control over User `John` is abused by making User `sam` its owner and write its DACL to grant Full control over User `John`, now being able to change its password, and so is done. 

---
###### `John` -> member of `Remote Management Users`: WinRM shell
User `John` being a member of "`Remote Management Users"` enables remote connection to the target system via WinRM. (user.txt)

---
###### `John` -> `GenericAll` -> `ADCS` OU:
**Restore "tombstoned" account (`cert_admin`)**:

On the other hand, `John` also holds `GenericAll` privilege over `ADCS` OU that, after BloodHound analysis, is discovered to hold a "tombstoned account" (concluded by BloodHound showing its SID and not its account name). This account (with SID: `S-1-5-21-1392491010-1358638721-2126982587-1111`) is restored to an active state using `Restore-ADObject` command from Windows system native PowerShell Module `ActiveDirectory`, via WinRM as `John`.

---
**Shadow credentials**:

With the account "revived" (now known to be User `cert_admin`), the `GenericAll` privilege over `ADCS` OU can be abused by employing Shadow Credentials technique, generating key pair, writing public key to `msDS-KeyCredentialLink` attribute of `cert_admin` account, and authenticating via Kerberos passwordless login PKINIT using the private key to sign a challenge that pairs to the written public key, allowing a successful authentication, capturing the TGT and with it the User `cert_admin` NT Hash.

---
##### Privilege Escalation: ESC15 + `cert_admin` enrollment rights: Write privileged application policies over cert request (CSR)
Enumerating ADCS with now controlled User `cert_admin`, a `WebServer` template is discovered to be vulnerable to ESC15 (CVE-2024-49019), meaning CA fails to validate application policies supplied in a certificate request (CSR). Paired with the `cert_admin` privilege to request mentioned template is abused by writing "Certificate Request Agent" over application policies to the certificate request, requesting and obtaining this privileged certificate. This enrollment agent certificate enables to request and specify UPN, therefore obtaining another certificate for Client Authentication with UPN `administrator`. The certificate is used to authenticate to the domain as `administrator`, capturing the TGT and retrieving the `administrator`'s NT Hash. Now with the `administrator` account controlled the domain is near Full compromise.

---
### Techniques:
- ACL Abuse:
	- WriteSPN over User Abuse - Targeted Kerberoast
	- AddSelf over Group Abuse - Add user to group
	- ReadGMSAPassword over Machine Abuse - gMSA Dump
	- ForceChangePassword over User Abuse- Reset user password
	- WriteOwner over User Abuse - Grant Ownership & Full Control > Change password / Set SPN
- Bloodhound enumeration with rusthound and certipy - Certificates and templates analysis
- Identify and Revive tombstoned account - Restore with AD PS Module
- Shadow credentials
- Schema version v1 template. ESC15 / CVE-2024-49019 - Inject privileged application policy (`Certificate Request Agent`) to CSR, then request administrator certificate for client authentication.
