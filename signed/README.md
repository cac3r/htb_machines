## Signed
### Info:

- Name:       **Signed**
- OS:         **Windows**
- Type:       **Assumed Compromise**
- Difficulty: **Medium**
- Status:     **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/signed/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/signed/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/signed/attack_chain.png)   - Attack chain diagram
- **`screenshots/`**           - Supporting screenshots

---
### Brief:
##### Pivot -> `mssqlsvc`: `xp_dirtree` + capture Hash
Starting the Assumed Compromise test on DC01.signed.htb using the given credentials for User `scott`. After network/host reconnaissance, authenticated to MSSQL service use the command `xp_dirtree` to call a SMB resource pointing at an attacker system, capturing the authentication and the service account `mssqlsvc`'s NetNTLMv2 Hash with responder SMB server. The Hash is cracked to recover the plaintext password. 
##### Privilege escalation: Forge kerberos ticket with objects RIDs
In order to escalate privileges in the MSSQL shell, get the `administrator` SID, it's RID and SID Domain prefix, plus adding other values like a user's NT hash (converted from `mssqlsvc` password), known groups RID (Domain Admins and Domain Users), any SPN (trivial service name) to forge a Kerberos ticket with administrator privileges, although, after connecting, seeing the db session is still as guest. Enumerating session types and targeting IT group for having sysadmin rights, adding its RID (1105) to forge a new ticket. With this last ticket connecting to MSSQL as dbo/sysadmin now enabling `xp_cmdshell` achieving RCE. 
###### Reverse Shell: MSSQL `xp_cmdshell`+ b64 cradle calling ps1 payload
Editing Nishang's `Invoke-PowershellTcpOneLine.ps1` including the attacker IP and port. Creating a base64 encoded "cradle" that calls the mentioned .ps1 payload on the attacker HTTP server. Executing the the encoded command "cradle" via MSSQL shell, obtaining the sent remote connection with a listener and now on a system shell as `mssqlsvc`. (user.txt)
###### Reading administrator directory: MSSQL `OPENROWSET BULK`
Adding `mssqlsvc` RID to a new ticket, absue the permission for this account to read the `administrator` directory with `OPENROWSET BULK` command. (root.txt)

---
### Techniques:
- MSSQL `xp_dirtree` abuse - Hash capture with responder SMB server
- Forge Kerberos Ticket - Obtaining objects SIDs and RIDs from MSSQL
- Reverse Shell with b64 encoded cradle and nishang PowerShell payload
- Use of MSSQL `OPENROWSET BULK` to read administrator directory
