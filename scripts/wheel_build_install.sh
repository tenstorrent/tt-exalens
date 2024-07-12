#! /bin/bash

make clean
make build
make dbd/wheel_release

pip uninstall debuda
pip install build/debuda_wheel/*.whl
