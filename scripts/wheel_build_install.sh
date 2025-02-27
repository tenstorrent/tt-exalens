#! /bin/bash

make clean
make build
make wheel

pip uninstall ttexalens -y
pip install build/ttlens_wheel/*.whl
