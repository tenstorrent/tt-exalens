#! /bin/bash

make clean
make build
make wheel

pip uninstall tt-lens
pip install build/ttlens_wheel/*.whl
