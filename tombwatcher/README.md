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
- ADCS Enrollment Agent abuse - ESC3, Crafting certificates
- ESC15 / CVE-2024-49019
