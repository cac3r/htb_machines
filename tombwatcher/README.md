## TombWatcher

### Info:
- Name: TombWatcher
- OS: Windows
- Type: Assumed Compromise
- Difficulty: Medium
- Status: Retired

### Content:
- `testing.md`                - Raw notes / working log
- `report.pdf`                - Professional report
- `attack_chain.png`  - Attack chain diagram
- `screenshots/`           - Supporting screenshots

### Techniques:
- ACL Abuse:
	- WriteSPN over User Abuse - Targeted Kerberoast
	- AddSelf over Group Abuse - Add user to group
	- ReadGMSAPassword over Machine Abuse - gMSA Dump
	- ForceChangePassword over User Abuse- Reset user password
	- WriteOwner over User Abuse - Grant Ownership & Full Control > Change password / Set SPN
- Bloodhound enumeration with rusthound - Certificates analysis
- Identify and Revive tombstoned account - Restore with AD PS Module
- Shadow credentials
- ADCS Enrollment Agent abuse - ESC3, Crafting certificates
- ESC15 / CVE-2024-49019
