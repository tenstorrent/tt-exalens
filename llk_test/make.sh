make clean
make VERBOSE=1 format=FORMAT_FLOAT16 mathop=ELTWISE_BINARY_ADD testname=eltwise_add_test arch=wormhole
make dis testname=eltwise_add_test
python3 debuda_test.py