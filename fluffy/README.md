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

### Techniques:
- CVE-2025-24071 - Malicious ZIP file upload - User triggered - NetNTLMv2 Hash capture
- GenericAll over Group Abuse - Add user to Group
- GenericWrite over Users Abuse - Shadow Credentials - NT Hash
- ESC16 Abuse - Write administrator UPN over account - Request cert as administrator - NTLM Hash
