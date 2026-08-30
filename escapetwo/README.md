## EscapeTwo

### Info:
- Name: EscapeTwo
- OS: Windows
- Type: Assumed Compromise
- Difficulty: Easy
- Status: Retired

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/escapetwo/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

### Techniques:
- MSSQL RCE > Reverse Shell
- WriteOwner over User Abuse - Shadow Credentials
- ESC4 permission over template Abuse - make it ESC1 vulnerable
- ESC1 vulnerable template Abuse - Inject administrator UPN, privileged cert
