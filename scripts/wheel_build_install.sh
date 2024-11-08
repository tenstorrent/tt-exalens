#! /bin/bash

make clean
make build
make wheel

pip uninstall tt-lens
pip install build/debuda_wheel/*.whl
