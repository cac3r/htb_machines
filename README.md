## HTB Machines

My [Hack The Box](https://www.hackthebox.com/) writeups and notes (**retired** machines only). 

Each machine folder has a raw working log, a clean report, and the attack chain diagram.


### Machines

| Machine | OS | Difficulty | Type | User | Root | Dependence | Time | Date | 
|---------|-----|-----------|------|----------|-------|------|-----|----|
| [Signed](./signed) | Windows | Medium | Assumed Compromise | X | X | Referenced | 3h 10min |2026-08-18
| [TombWatcher](./tombwatcher) | Windows | Medium | Assumed Compromise | X | X | Referenced | 6h 15min |2026-08-20/21


---

#### Dependence legend

How much outside help each box took:

- **Solo** — start to finish with my own methodology and research
- **Hint** — got unstuck with writeup/video at a single point, then continued on my own
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
