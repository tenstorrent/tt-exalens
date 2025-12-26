# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens import init_ttexalens, write_words_to_device, read_word_from_device, OnChipCoordinate, Device
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug


context = init_ttexalens()


def make_tensix_work(location: OnChipCoordinate):
    noc_block = location.noc_block
    for risc_debug in noc_block.debuggable_riscs:
        assert isinstance(risc_debug, BabyRiscDebug)
        write_words_to_device(location, risc_debug.risc_info.get_code_start_address(risc_debug.register_store), 0x6F)
        risc_debug.set_reset_signal(False)
        assert not risc_debug.is_in_reset(), f"RISC {risc_debug.risc_location.risc_name} is in reset."


def make_all_tensix_work(device: Device):
    for location in device.get_block_locations("functional_workers"):
        make_tensix_work(location)


def test_tensix_reset(location: OnChipCoordinate):
    try:
        location.noc_block.reset()
        device = location.device
        noc_block = device.get_block(location)
        assert noc_block.supports_reset(), f"NoC block at location {location} does not support reset."
        noc_block.reset()

        # Verify that all RISCs are in reset
        for risc_debug in noc_block.debuggable_riscs:
            assert risc_debug.is_in_reset(), f"RISC {risc_debug.risc_location.risc_name} is not in reset."

        # Verify that all other noc locations don't have riscs in reset
        for other_loc in device.get_block_locations("functional_workers"):
            if other_loc != location:
                other_noc_block = device.get_block(other_loc)
                for risc_debug in other_noc_block.debuggable_riscs:
                    assert (
                        not risc_debug.is_in_reset()
                    ), f"RISC {risc_debug.risc_location.risc_name} at location {other_loc} is in reset."

        # Put all RISCs back to running state for next iteration
        for risc_debug in noc_block.debuggable_riscs:
            assert isinstance(risc_debug, BabyRiscDebug)
            write_words_to_device(
                location, risc_debug.risc_info.get_code_start_address(risc_debug.register_store), 0x6F
            )
            risc_debug.set_reset_signal(False)
            assert not risc_debug.is_in_reset(), f"RISC {risc_debug.risc_location.risc_name} is in reset."
        return True
    except Exception as e:
        return False


def test_device(device: Device):
    print(f"Testing device: {device._id}")
    make_all_tensix_work(device)
    for location in device.get_block_locations("functional_workers"):
        if test_tensix_reset(location):
            print(f"+ Reset successful for functional worker at location {location.to_user_str()}.")
        else:
            print(f"- Reset failed for functional worker at location {location.to_user_str()}.")
            global context
            device_id = location.device_id
            context.server_ifc.warm_reset()
            context = init_ttexalens()
            make_all_tensix_work(context.devices[device_id])


for device in context.devices.values():
    test_device(device)
