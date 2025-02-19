# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
This file contains the class for the coordinate object. As we use a number of coordinate systems, this class
is used to uniquely represent one grid location on a chip. Note that not all coordinate systems have a 1:1
mapping to the physical location on the chip. For example, not all noc0 coordinates have a valid netlist
coordinate. This is due to the fact that some locations contain non-Tensix tiles, and also since some Tensix
rows may be disabled due to harvesting.

The following coordinate systems are available to represent a grid location on the chip:

  - die:            represents a location on the die grid. This is a "geographic" coordinate and is
                    not really used in software. It is often shown in martketing materials, and shows the
                    layout in as in <arch>-Noc-Coordinates.xls spreadsheet, and on some T-shirts.
  - noc0:           NOC routing coordinate for NOC 0. Notation: X-Y. Also known as "physical" coordinate.
                    Represents the chip location on the NOC grid. A difference of 1 in NOC coordinate
                    represents a distance of 1 hop on the NOC. In other words, it takes one clock cycle
                    for the data to cross 1 hop on the NOC. Furthermore, the NOC 'wraps around' so that
                    the distance between 0 and NOC_DIM_SIZE-1 is also 1 hop. As we have 2 NOCs, we have
                    2 NOC coordinate systems: noc0 and noc1.
  - noc1:           NOC routing coordinate for NOC 1. Notation: X-Y
                    Same as noc0, but using the second NOC (which goes in the opposite direction).

  The above three do not depend on harvesting. They only depend on the chip architecture. Also, they share
  the extents in both X (column) and Y (row). The following coordinates depend on the harvesting mask.
  See https://github.com/tenstorrent/tt-umd/blob/main/docs/coordinate_systems.md for more details on coordinate systems.

  - logical:        Logical grid coordinate. Notation: X,Y.
                    This coordinate system is mostly used to reference Tensix cores, since this cores are most frequently
                    accessed. This coordinate system hides the details of physical coordinates and allows upper layers of
                    the stack to access Tensix endpoints through a set of traditional Cartesian Coordinates. This coordinate
                    systems has very simple indexing, it starts from 0,0 and ends at (X-1),(Y-1) where X and Y is
                    number of cores on x-axis and y-axis, respectively.
                    Since the logical coordinate system includes core type information, it is possible to have multiple
                    same coordinates with different core types. For example, (0,0) can be a tensix core, an eth core, or a dram core.
                    In order to differentiate between these, first letter is included in string coordinate. Examples:
                    e0,0 for eth core, t0,0 for tensix core, d0,0 for dram core. If you use 0,0, it will be considered as tensix core.
  - virtual:        Virtual NOC coordinate. Similar to noc0, but with the harvested rows moved to the end, and the locations of
                    functioning rows shifted down to fill in the gap. This coordinate system is used to communicate with
                    the driver. Notation: X-Y.
  - translated:     Translated NOC coordinate. Similar to virtual, but offset by 16 on wormhole. Notation: X-Y
                    This system is used by the NOC hardware to account for harvesting. On wormhole, translated coordinates will
                    start at 16, 16. It is also constructed such that starting with (18,18) maps exactly to the logical tensix
                    grid. It is used by the NOC hardware and it is programmable ahead of time. Notation: X-Y
"""

from ttlens.util import TTException

VALID_COORDINATE_TYPES = [
    "die",
    "noc0",
    "physical",
    "noc1",
    "logical",
    "logical-tensix",
    "logical-eth",
    "logical-dram",
    "virtual",
    "translated",
]


class CoordinateTranslationError(Exception):
    """
    This exception is thrown when a coordinate translation fails.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"CoordinateTranslationError: {self.message}"


class OnChipCoordinate:
    """
    This class represents a coordinate on the chip. It can be used to convert between the various
    coordinate systems we use.
    """

    _noc0_coord = (None, None)  # This uses noc0 coordinates: (X,Y)
    _device = None  # Used for conversions

    def __init__(self, x: int, y: int, input_type: str, device, core_type="any"):
        """
        Constructor for the Coordinate class.

        Args:
            x (int): The x-coordinate value.
            y (int): The y-coordinate value.
            input_type (str): The input coordinate system type. One of the following:
                - noc0: NOC routing coordinate for NOC 0. (X-Y). Also known as "physical" coordinate.
                - noc1: NOC routing coordinate for NOC 1. (X-Y)
                - die: Die coordinate, a location on the die grid. (X,Y)
                - logical: Logical grid coordinate. Notation: qX,Y, where q represents first letter of the core type. If q is not present, it is considered as tensix core.
                - virtual: Virtual NOC coordinate. Similar to noc0, but with the harvested rows removed, and the locations of functioning rows shifted down to fill in the gap. (X-Y)
                - translated: Translated NOC coordinate. (X-Y)
            device: The device object used for coordinate conversion.
            core_type (str, optional): The core_type used for coordinate conversion. Some coordinate systems require core_type as third dimension. Defaults to "any".

        Raises:
            Exception: If the input coordinate system is unknown.

        Notes:
            - If the device is not specified, coordinate conversion to other systems will not be possible.
        """
        assert device is not None
        self._device = device
        if input_type == "noc0" or input_type == "physical":
            self._noc0_coord = (x, y)
        elif input_type == "virtual":
            self._noc0_coord = self._device.to_noc0((x, y), "virtual", core_type)
        elif input_type == "noc1":
            self._noc0_coord = self._device.to_noc0((x, y), "noc1", core_type)
        elif input_type == "die":
            self._noc0_coord = self._device.to_noc0((x, y), "die", core_type)
        elif input_type == "logical":
            self._noc0_coord = self._device.to_noc0((x, y), "logical", core_type)
        elif input_type == "translated":
            self._noc0_coord = self._device.to_noc0((x, y), "translated", core_type)
        else:
            raise Exception("Unknown input coordinate system: " + input_type)

    # This returns a tuple with the coordinates in the specified coordinate system.
    def to(self, output_type):
        """
        Returns a tuple with the coordinates in the specified coordinate system.

        Args:
            output_type (str): The desired output coordinate system.

        Returns:
            tuple: The coordinates in the specified coordinate system.

        Raises:
            Exception: If the output coordinate system is unknown.
        """
        if output_type == "noc0" or output_type == "physical":
            return self._noc0_coord
        elif output_type == "virtual":
            return self._device.from_noc0(self._noc0_coord, "virtual")[0]
        elif output_type == "noc1":
            return self._device.from_noc0(self._noc0_coord, "noc1")[0]
        elif output_type == "die":
            return self._device.from_noc0(self._noc0_coord, "die")[0]
        elif output_type == "logical":
            return self._device.from_noc0(self._noc0_coord, "logical")
        elif output_type == "translated":
            return self._device.from_noc0(self._noc0_coord, "translated")[0]
        elif output_type.startswith("logical-"):
            core_type = output_type.split("-")[1]
            coord = self._device.from_noc0(self._noc0_coord, "logical")
            if coord[1] == core_type:
                return coord[0]
            else:
                raise Exception(
                    f"Coordinate (noc0 {self._noc0_coord[0]}-{self._noc0_coord[1]}: {coord[1]}) is not supported in coordinate sub-system {output_type}"
                )
        else:
            raise Exception("Unknown output coordinate system: " + output_type)

    # Which axis is used to advance in the horizontal direction when rendering the chip
    # For X-Y coordinates, this is the X, for R,C coordinates, this is the C.
    def horizontal_axis(coord_type):
        return 0

    def vertical_axis(coord_type):
        return 1 - OnChipCoordinate.horizontal_axis(coord_type)

    def vertical_axis_increasing_up(coord_type):
        return False

    def to_str(self, output_type="noc0"):
        """
        Returns a tuple with the coordinates in the specified coordinate system.
        """
        try:
            output_tuple = self.to(output_type)
        except CoordinateTranslationError as e:
            return "N/A"

        if output_type == "logical":
            core_type = output_tuple[1]
            output_tuple = output_tuple[0]
            if core_type == "tensix":
                return f"{output_tuple[0]},{output_tuple[1]}"
            else:
                return f"{core_type[0]}{output_tuple[0]},{output_tuple[1]}"

        if output_type == "die":
            return f"{output_tuple[0]},{output_tuple[1]}"
        return f"{output_tuple[0]}-{output_tuple[1]}"

    def to_user_str(self):
        """
        Returns a string representation of the coordinate that is suitable for the user.
        """
        noc0 = self.to_str("noc0")
        logical = self.to_str("logical")
        return f"{noc0} ({logical})"

    def change_device(self, device):
        """
        Returns coordinates for the specified device.

        Args:
            device (Device): The device object representing the chip.

        Returns:
            OnChipCoordinate: The new coordinate object for the specified device.
        """
        # If the device is the same, return the same object
        if device == self._device:
            return self

        # Try to convert to logical coordinates. If that fails, fallback to translated coordinates.
        # We cannot use noc0 coordinates because of harvesting.
        try:
            logical = self.to("logical")
            logical_tuple = logical[0]
            return OnChipCoordinate(logical_tuple[0], logical_tuple[1], "logical", device, logical[1])
        except CoordinateTranslationError:
            translated_tuple = self.to("translated")
            return OnChipCoordinate(translated_tuple[0], translated_tuple[1], "translated", device)

    # The default string representation is the logical coordinate. That's what the user deals with.
    def __str__(self) -> str:
        return self.to_str("logical")

    def __hash__(self):
        return hash((self._noc0_coord, self._device._id))

    # The debug string representation also has the translated coordinate.
    def __repr__(self) -> str:
        return self.to_user_str()

    def full_str(self) -> str:
        return f"noc0: {self.to_str('noc0')}, noc1: {self.to_str('noc1')}, die: {self.to_str('die')}, logical: {self.to_str('logical')}, translated: {self.to_str('translated')}, virtual: {self.to_str('virtual')}"

    # == operator
    def __eq__(self, other):
        # util.DEBUG("Comparing coordinates: " + str(self) + " ?= " + str(other))
        return (self._noc0_coord == other._noc0_coord) and (self._device == other._device)

    def __lt__(self, other):
        if self._device.id() == other._device.id():
            return self._noc0_coord < other._noc0_coord
        else:
            return self._device.id() < other._device.id()

    def create(coord_str, device, coord_type=None):
        """
        Creates a coordinate object from a string. The string can be in any of the supported coordinate systems.

        Parameters:
            coord_str (str): The string representation of the coordinate.
            device (Device): The device object representing the chip.
            coord_type (str, optional): The type of coordinate system used in the string.
                If not specified, it will be determined based on the separators used in the string.

        Returns:
            OnChipCoordinate: The created coordinate object.

        Raises:
            Exception: If the coordinate format is unknown or invalid.

        Supported coordinate formats:
            - X-Y format: The coordinates are separated by a hyphen ("-"). Example: "10-20"
            - R,C format: The coordinates are separated by a comma (","). Example: "10,20"
            - DRAM channel format: The coordinate starts with "CH" followed by the channel number.
              Example: "CH1"

        Note:
            - If the coordinate format is X-Y or R,C, the coordinates will be converted to integers.
            - If the coordinate format is DRAM channel, the corresponding NOC0 coordinates will be used.
        """

        if "-" in coord_str:
            core_type = "any"
            x, y = coord_str.split("-")
            x = int(x.strip())
            y = int(y.strip())
            if coord_type is None:
                coord_type = "translated" if device.is_translated_coordinate(x, y) else "noc0"
        elif "," in coord_str:
            # Try to get core type from coord_str
            core_type = "tensix"  # If letter that explains core type is not present, we will default to tensix
            core_types = device.core_types
            for ct in core_types:
                if coord_str[0:1].lower() == ct[0:1]:
                    core_type = ct
                    coord_str = coord_str[1:]
                    break
            if coord_type is None:
                coord_type = "logical"
            x, y = coord_str.split(",")
            x = int(x.strip())
            y = int(y.strip())
        elif coord_str[0:2].upper() == "CH":  # This is a DRAM channel
            # Parse the digits after "CH"
            x = int(coord_str[2:])
            y = 0
            core_type = "dram"
            coord_type = "logical"
        else:
            raise TTException("Unknown coordinate format: " + coord_str + ". Use either X-Y or R,C")

        return OnChipCoordinate(x, y, coord_type, device, core_type)
