#! /bin/bash

make clean
make build
make wheel

pip uninstall debuda
pip install build/debuda_wheel/*.whl
