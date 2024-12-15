# TTLens JTAG Tutorial
This tutorial shows you how to set up and use JTAG.

## Licensing
The JTAG library is proprietary and subject to licensing restrictions. Access is currently limited to employees only.

## Installation
#### Downloading
To get the JTAG library you will need to run:
```
./scripts/get_jtag_access_library.sh
```
This will download library from private gitlab repository and place it in ``third_party/jtag_access_library/``.

#### Building
After downloading the library for the first time, run:
```
make clean
make
```
so that CMake knows that we have JTAG, and it will include it in all subsequent builds.

#### Python wheel
If you additionally want to use JTAG in ttlens python library, after you installed wheel package using ```pip install```, you will also need to run
```
./scripts/add_libjtag_to_wheel.sh
```

#### Permissions
Your user will need to have permission for using SEGGER jlink adapter.
```
$ cat /etc/udev/rules.d/99-usb.rules

# SEGGER (jlink JTAG adapter)
SUBSYSTEM=="usb", ATTR{idVendor}=="1366", ATTR{idProduct}=="*", MODE="0666"
```

## Usage
### Library
Library will need to be initialized with init_jtag parameter.
```
init_ttlens(init_jtag=True)
```


### App
To use JTAG in the ttlens app, you will need to add ```--jtag``` parameter to command.
```
./tt-lens.py --jtag
tt-lens --command "brxy 0,0 0" --jtag
tt-lens --server --jtag
```

## Organization
When ttlens is run with JTAG support you will not be able to access cards over PCI in that instance.
Only visible chips in ttlens are the ones that you connected JTAG to.

For example if we connected to an n300 card, without JTAG we would see "Device 0" and "Device 1" which are chips on that card.
On the same card, depending of the number of connected JTAG devices we will see "Device JTAG0" and/or "Device JTAG1"...

To make a correlation between chips accessed by JTAG and PCI, we can use the ```interfaces``` command.
In context of ttlens "Device" is a unique chip accessed via one of the interfaces.

```
tt-lens --command "if; x" --jtag

JTAG Device 0: {'lot_id': '8IPY38007', 'wafer_id': '.13B2', 'wafer_alias': '', 'x_coord': '005', 'y_coord': '00', 'binning': '', 'test_program_rev': ''}
```

```
tt-lens --command "if; x"

NOC Device 0: {'lot_id': '8IPY38007', 'wafer_id': '.13B2', 'wafer_alias': '', 'x_coord': '005', 'y_coord': '00', 'binning': '', 'test_program_rev': ''}
NOC Device 1: {'lot_id': '8IPY38007', 'wafer_id': '.12B7', 'wafer_alias': '', 'x_coord': '001', 'y_coord': '00', 'binning': '', 'test_program_rev': ''}
PCI Device 0: {'lot_id': '8IPY38007', 'wafer_id': '.13B2', 'wafer_alias': '', 'x_coord': '005', 'y_coord': '00', 'binning': '', 'test_program_rev': ''}
```

With the output we can see that we connected JTAG to mmio chip.
JTAG Device 0 unique identification is same as NOC Device 0 (That is also a PCI Device).
That means that commands targeting "Device 0" and "Device JTAG0" will have the same behavior.

Other than that, usage should be exactly the same, all supported library functions can and will be used via either PCI or JTAG depending on the parameter provided at start.
