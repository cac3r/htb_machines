### Info:
- Name: **Multimaster**
- OS: **Windows**
- Type: **Unauthenticated**
- Difficulty: **Insane**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/multimaster/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/multimaster/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/multimaster/attack_chain.png)   - Attack chain diagram
- [**`text2unicodeescape.py`**](https://github.com/cac3r/htb_machines/blob/main/multimaster/text2unicodeescape.py)   - Python script
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Recon & Enumeration
Starting the test against the target system DC `multimaster` unauthenticated. After host reconnaissance and basic unauthenticated domain enumeration, browse HTTP to enumerate the website exposed at port 80/tcp (`http://multimaster.megacorp.htb`), which is a employee social hub for the target company. In this website, discover a function to search members (colleagues). Searching with a blank / empty input, the function disclose 17 potential valid domain accounts, which result to 14 valid ones after validating them against Kerberos authentication.
#### Initial access: UNION based SQLi unicode escape encoded - disclosure of Passwords hashes
Intercept the HTTP request to search members, `/api/colleagues`, with BurpSuite proxy. Probing this function JSON parameter "`name`" can observe special characters being blocked, returning a 403 forbidden response. Making use of Turbo Intruder extension to make requests sending special characters, discover that repetitive, fast requests eventually triggers a block, returning 403 during a period of time while being blocked (around 1 minute). Adjusting Turbo Intruder script to delay requests for half a second, the scan requests go unblocked, and results indicate `\` character returns an odd 500 internal server error and decide to start probing for SQL injection. Queries are blocked, responses return 403, SQL syntax / words are being blocked. 

*(Referenced)* Unicode Escape encoding bypasses WAF (Web Application Firewall) blocks . 

Encoding queries (first manually with word to word converter and later with python script for whole query), use `order by x` and find the original query calls 5 columns. With `union select x,y,z,...` can start to enumerate the database, retrieving version / type - MSSQL 2017; Databases - `Hub_DB`, ...; Tables - `Logins`, ...; Columns - `username`, `password`, ... With this information dump all rows of `Logins` table and disclose 17 hashes, but out of them only 3 are unique, passwords are reused between accounts. Using hashcat identify 4 possible hash types and modes to crack, trying each, hashes are cracked with mode `17900` ("Keccak-384") retrieving 3 plaintext passwords. None valid for any of the previously discovered domain accounts.
#### Domain accounts disclosure - MSSQL RID brute forcing via SQLi
*(Referenced)* The SQLi point can be used to abuse legitimate MSSQL functions to discover more domain accounts via RID brute forcing.

Creating a python script to automate the RID brute force with the help of AI (Claude Opus 4.8) is taking a lot of time and after several tries find hard to make it work.

*(Cheat)* 2 accounts are found via RID brute force. `tushikikatomo` and `andrew`.

Checking the 2 discovered accounts against the previously cracked passwords from database, turns out with a valid domain credential. `tushikikatomo:finance1`. As this account is a member of Remote Management Users group, can connect to the target system via exposed WinRM service and establish a shell as `tushikikatomo`. (user.txt)

---
---
### Techniques:
- Domain accounts validation via Kerberos
- UNION based SQLi with WAF bypass using unicode escape and time delay
	- Enumerate database -> Password hashes
	- Enumerate domain users via RID brute forcing -> Domain accounts
- BloodHound enumeration with SharpHound collector
