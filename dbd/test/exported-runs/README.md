## gs-x2-fd8f98aca.zip - Kyle's run from checkout fd8f98aca
Rerun:
make -j32 verif/netlist_tests/test_inference
ARCH_NAME=grayskull ./build/test/verif/netlist_tests/test_inference --netlist verif/graph_tests/netlists/netlist_encoder_x4_2gs.yaml --backend Silicon --seed 0 --num-loops 2
