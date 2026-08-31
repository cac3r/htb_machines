## HTB Machines

My [Hack The Box](https://www.hackthebox.com/) writeups and notes (**retired** machines only). 

Each machine folder has a raw working log, a clean report, and the attack chain diagram.


### Machines

| Machine | OS | Difficulty | Type | User | Root | Dependence | Time | Date | 
|---------|-----|-----------|------|----------|-------|------|-----|----|
| [Fluffy](./fluffy) | Windows | Easy | Assumed Compromise | X | X | Hint | 3h 55min |2026-08-30/31
| [EscapeTwo](./escapetwo) | Windows | Easy | Assumed Compromise | X | X | Referenced | 4h 20min |2026-08-24/25/26/27
| [TombWatcher](./tombwatcher) | Windows | Medium | Assumed Compromise | X | X | Referenced | 6h 15min |2026-08-20/21
| [Signed](./signed) | Windows | Medium | Assumed Compromise | X | X | Referenced | 3h 10min |2026-08-18


---

#### Dependence legend

How much outside help each box took:

- **Solo** — start to finish with my own methodology and research (no walkthrough/video. Web Browsing applies)
- **Hint** — got unstuck with writeup/video at a single point, just a hint for direction/debugging
- **Referenced** — followed a writeup/video at some point

#### Per-machine structure

```
MachineName/
├── README.md          # machine info, repo index and techniques
├── testing.md         # raw working log
├── report.pdf         # clean professional report
├── attack_chain.png   # attack chain diagram
└── screenshots/       # supporting screenshots
```
