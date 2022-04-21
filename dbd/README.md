# Buda Debug Interface and Tools


[Documentation](https://tenstorrent.sharepoint.com/:f:/r/sites/Specifications/Spatial/Debug?csf=1&web=1&e=m6PtgT]) on Sharepoint:
- [Debug architecture](https://tenstorrent.sharepoint.com/:w:/r/sites/Specifications/Spatial/Debug/buda_debug_architecture.docx?d=w314badcf8d404f4b92e083091b0edad5&csf=1&web=1&e=EEX4UD)
- [Presentation](https://tenstorrent.sharepoint.com/:p:/r/sites/Specifications/Spatial/Debug/buda-debug-infra.pptx?d=wb835600fe80c44b79831eecb58290533&csf=1&web=1&e=r6m3Ux)

Source code path: **dbd/**.
Main development branch: **ihamer/debuda**.

List of all [Debuda issues](https://yyz-gitlab.local.tenstorrent.com/tenstorrent/budabackend/-/issues?scope=all&state=opened&label_name[]=Debuda). Gitlab issues label: **debuda**.

## Debuda.py - silicon debugging

![High level diagram](docs/images/debuda.png)

Debuda.py is used to probe hardware and detect/trace hangs in NOC, get status of Queues, contents of memory, status of Riscs.
It has access to NOC registers, DRAM, L1, host-based queues.

Prints status of streams.

### Building debuda-stub
```
bin/build-debuda-stub.sh
```
Prebuilt binary is committed to git repo for convenience.