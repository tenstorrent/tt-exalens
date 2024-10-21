import numpy as np

def float_to_byte_array(value, format):
    if format == "Float16_b":
        # Convert to float32
        float_value = np.float32(value)
        # Get the bits and keep the upper 16 bits for bfloat16
        bfloat16_bits = float_value.view(np.uint32) >> 16
        # Create a byte array of length 4, filling the first two bytes with bfloat16 bits
        byte_array = np.array([bfloat16_bits], dtype=np.uint32).tobytes()[:2] + b'\x00\x00'
    elif format == "Float16":
        # Convert to float16
        float_value = np.float16(value)
        byte_array = float_value.tobytes()

    # Convert the byte array to a list of decimal values
    byte_list = list(byte_array)

    # Ensure there are 4 elements in the list
    if len(byte_list) < 4:
        byte_list += [0] * (4 - len(byte_list))  # Pad with zeros if less than 4
    elif len(byte_list) > 4:
        byte_list = byte_list[:4]  # Truncate if more than 4

    return byte_list[::-1]  # Reverse the byte order

def read_floats_from_bytes(byte_array, k):
    if len(byte_array) != 4:
        raise ValueError("Input must be an array of four bytes.")
    
    # Combine bytes into a single 32-bit integer
    int_value = (byte_array[0] << 24) | (byte_array[1] << 16) | (byte_array[2] << 8) | byte_array[3]
    
    # Convert to float16
    float16_bytes = int_value.to_bytes(2, byteorder='little')
    float16_value = np.frombuffer(float16_bytes, dtype=np.float16)[0]
    
    # Convert to bfloat16
    bfloat16_value = np.frombuffer(int_value.to_bytes(4, byteorder='little'), dtype=np.uint16)[0]
    bfloat16_value = np.float32(bfloat16_value)  # Cast it to float32 for proper interpretation
    
    if(k == 1):
        return float16_value
    else:
        return bfloat16_value

# Example usage
a = float_to_byte_array(8.5, "Float16_b")
b = float_to_byte_array(8.5, "Float16")
aa = read_floats_from_bytes(a,1)
bb = read_floats_from_bytes(b,2)

print("Byte array for bfloat16:", a)
print("Byte array for float16:", b)
print("Converted back from bfloat16:", aa)
print("Converted back from float16:", bb)
