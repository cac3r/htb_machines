## Fluffy

### Info:
- Name: **Fluffy**
- OS: **Windows**
- Type: **Assumed Compromise**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/fluffy/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/fluffy/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/fluffy/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
### Brief:
##### Foothold: CVE-2025-24071
Starting the Assumed Compromise test on DC01.fluffy.htb using the given credentials for User `j.fleischman`. After network/host reconnaissance, authenticated to the exposed SMB service, discover READ and WRITE access to `IT` Share. This Share contains a PDF file for a previous vulnerability report containing a list of CVEs presumably found on the target system. Searching information about this CVEs on the internet find and use CVE-2025-24071 (second in the PDF list) that let's an attacker craft a malicious RAR/ZIP file that, at the point of extraction (unzip), Windows system tries to index the resource pointing to attacker's IP, triggering a SMB authentication (as the user that performed the action: `p.agila`) reaching the attacker controlled server, capturing and saving the user's NetNTLMv2 Hash. The Hash is cracked to recover the plaintext password. 
##### Domain escalation/pivot: ACL abuse, Shadow Credentials
Enumerating the Domain with BloodHound find a chain of privileges that potentially leads to service accounts with other and more interesting rights. 
User `p.agila` (now controlled by attacker) is a member of  "Service Account Managers", a Group with `GenericAll` control over "Service Accounts" enabling to add any Domain User to the second group, and so is done with `p.agila`. Now as a member of "Service Accounts" Group can abuse `GenericWrite` over privileged service accounts `ca_svc` and `winrm_svc`, writing attacker generated public key over `msDS-KeyCredentialLink` account configuration field in both accounts to then authenticate sending a challenge signed with the generated private key, capturing the TGT and retrieving the NT hash for both mentioned accounts. 
As a member of "Remote Management Users", `winrm_svc` account is used to establish a remote connection to the target system via WinRM (using the NT Hash, "PtH"), at this point enabling command execution as `winrm_svc`.
##### Privilege escalation: ESC16 + GenericWrite over User with Client Auth enrollment rights -> UPN template injection and certificate request
On the other hand, enumerating ADCS and certificate templates as `ca_svc` find the presence of ESC16, a missing security extension for ADCS that should be enabled to map user identity in certificate requests via SID (Security Identifier). With A. ESC16 present, B. `p.agila` account (member of "Service Accounts" at this point) `GenericWrite`  control over `ca_svc`, and C. `ca_svc` having enrollment rights over Client Authentication template, an attacker can inject a privileged user's (`administrator`) UPN to a certificate request, and after reverting the UPN back to account defaults to avoid the mismatch error due to 2 accounts having the same UPN, authenticate sending the obtained certificate, capturing the authentication TGT and therefore extracting the `administrator`'s NT Hash. At this point, an attacker can use the certificate and the NT hash to authenticate as `administrator` to domain services. The attacker connects via WinRM as `administrator` to complete the chain from a low-privileged user up to administrative entities inside the domain. Further Domain compromise could be achieved using post exploitation techniques such as DCSync.

---
### Techniques:
- CVE-2025-24071 - Malicious ZIP file upload - User triggered - NetNTLMv2 Hash capture
- GenericAll over Group abuse - Add user to Group
- GenericWrite over Users abuse - Shadow Credentials - NT Hash
- ESC16 + GenericWrite over User with Client Auth enrollment rights abuse - Write administrator UPN over account - Request cert as administrator - NTLM Hash
