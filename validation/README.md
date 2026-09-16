### Info:
- Name: **Validation**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/<>/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/<>/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/<>/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Foothold -> `www-data`: Reading and Writing files via SQLi with UNION queries reflecting data in response
Starting the test against the target system `validation` unauthenticated. After network/host reconnaissance, enumerating the exposed HTTP web service on port 80, observe a registration functionality where user inputs name and selects a country out of a list. Probing this request, find an error in the response reaction of a injected SQL UNION query. Using this injection point on the `country` parameter in `index.php` to read `config.php` (discovered by fuzzing), this later file leaking a database credential for the user `uhc`. In the same SQL injection point, abuse writting permission to write a malicious PHP file to the webroot, calling it specifying commands and resulting RCE as `www-data`, and furthermore, a shell after executing a simple bash reverse shell payload pointing to the attacker system, here read the user.txt flag. 
###### Privilege Escalation -> `root`: Database user `uhc` password reused for `root`
In this shell as `www-data`, switch user to `root`, input the discovered password for `uhc` and turns out valid, the password is reused. Now as `root` obtain the final root.txt flag.   

---
---
### Techniques:
- SQLi union query with reflected data in response
- Reading files via SQLi (MySQL)
- Writting a malicious file (PHP) via SQLi (MySQL) 
---
---
### Lesson:
Lesson #1: Try hardvested passwords against any known user/service, is cheap and quick, worst case is not valid. For now on will note the credentials on a separate file to have handy to copy paste passwords to check for reuse. 

Lesson #2: If you can read files via SQLi, also try to write files (example classic PHP file for RCE on PHP backend)
