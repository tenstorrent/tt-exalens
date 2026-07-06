# Tooling Safety Record — tt-exalens

| Field | Value |
|---|---|
| Tool name | TT-Lensium |
| Tool owner | Aleksandar Dordevic |
| Tool class | T2 due to use in LLK test infra (T4 otherwise?) |
| In scope | Yes - part used by LLK test infra |
| Intended use | Load a compiled code from RISC-V ELF onto RISC and executing it |
| Workflow stage | Read code from RISC-V ELF and write it to RISC's memory, deassert core |
| Inputs | ELF file, target RISC core/location |
| Outputs | Code from ЕLF executed by targeted RISC |
| Safety impact if wrong | Incorrect or partial program loaded onto the core → LLK tests run against the wrong/incomplete binary → invalid verification evidence accepted into a release |
| Independent check | Built-in read-back verification comparing written bytes against ELF section bytes|
| Version | 0.3.25 |
| Configuration lock | Pinned PyPI wheel version |
| Evidence produced | TT-Lensium and TT-LLK test logs |
| Evidence location | https://github.com/tenstorrent/tt-exalens and https://github.com/tenstorrent/tt-metal/tree/main/tt_metal/tt-llk |
| Usage constraints | / |
| Qualification rationale | / |
| Status | Draft |
| Last review date | 2026-07-06 |

---
