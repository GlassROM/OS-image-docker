#!/usr/bin/env python3

import subprocess
import re
import sys
import os

def run_avbtool_info(image_path):
    cmd = ['avbtool', 'info_image', '--image', image_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running avbtool: {result.stderr}")
        sys.exit(1)
    return result.stdout

def parse_avbtool_output(output):
    hashtree_descriptor = {}
    lines = output.splitlines()
    in_descriptor = False
    for line in lines:
        if 'Hashtree descriptor:' in line:
            in_descriptor = True
            continue
        if in_descriptor:
            if line.strip() == '':
                break  # End of descriptor
            match = re.match(r'\s*(.+?):\s*(.+)', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                hashtree_descriptor[key] = value
    return hashtree_descriptor

def calculate_target_length(image_size):
    return image_size // 512

def calculate_fec_params(hashtree_descriptor):
    fec_num_roots = int(hashtree_descriptor.get('FEC num roots', '0'))
    if fec_num_roots == 0:
        return None
    fec_offset_str = hashtree_descriptor['FEC offset']
    fec_size_str = hashtree_descriptor['FEC size']

    # Extract numeric values from strings
    fec_offset = int(fec_offset_str.split()[0])
    fec_size = int(fec_size_str.split()[0])

    fec_start_block = fec_offset // 512
    fec_blocks = fec_size // 512
    return {
        'fec_roots': fec_num_roots,
        'fec_start_block': fec_start_block,
        'fec_blocks': fec_blocks
    }

def get_partuuid_from_image(image_path):
    cmd = ['file', image_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running file command: {result.stderr}")
        sys.exit(1)
    output = result.stdout.strip()
    # Extract UUID from output
    match = re.search(r'uuid=([A-Fa-f0-9-]+)', output)
    if match:
        uuid = match.group(1)
        return uuid
    else:
        print("UUID not found in file command output.")
        sys.exit(1)

def construct_dm_verity_param(hashtree_descriptor, partuuid):
    # Extract numeric values
    image_size_str = hashtree_descriptor['Image Size']
    data_block_size_str = hashtree_descriptor['Data Block Size']
    hash_block_size_str = hashtree_descriptor['Hash Block Size']

    image_size = int(image_size_str.split()[0].replace(',', ''))
    data_block_size = int(data_block_size_str.split()[0])
    hash_block_size = int(hash_block_size_str.split()[0])

    hash_algorithm = hashtree_descriptor['Hash Algorithm']
    root_digest = hashtree_descriptor['Root Digest']
    salt = hashtree_descriptor['Salt']
    fec_params = calculate_fec_params(hashtree_descriptor)
    target_length = calculate_target_length(image_size)
    data_device = f'/dev/disk/by-partuuid/{partuuid}'
    hash_device = data_device  # Assuming data and hash are on the same device

    # Build the mapping table
    mapping_table = f"0 {target_length} verity 1 {data_device} {hash_device} {data_block_size} {hash_block_size} {hash_algorithm} {root_digest} {salt}"

    if fec_params:
        # Number of optional parameters is 4
        optional_params = 4
        mapping_table += f" {optional_params} {fec_params['fec_roots']} {fec_params['fec_blocks']} {fec_params['fec_start_block']} {data_device}"
    else:
        optional_params = 0

    # Build the dm parameter
    dm_param = f'dm="0 vroot none ro,0 1 {mapping_table}"'

    return dm_param

def main():
    if len(sys.argv) != 2:
        print("Usage: generate_kernel_cmdline.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' not found.")
        sys.exit(1)

    # Get the PARTUUID from the image
    partuuid = get_partuuid_from_image(image_path)

    # Run avbtool info_image
    avbtool_output = run_avbtool_info(image_path)

    # Parse the output
    hashtree_descriptor = parse_avbtool_output(avbtool_output)
    if not hashtree_descriptor:
        print("Hashtree descriptor not found in avbtool output.")
        sys.exit(1)

    # Construct the dm-verity parameter
    dm_param = construct_dm_verity_param(hashtree_descriptor, partuuid)

    # Add root parameter
    root_param = 'root=/dev/mapper/vroot'

    # Combine parameters
    kernel_cmdline = f"{dm_param} {root_param}"

    print(kernel_cmdline)

if __name__ == '__main__':
    main()
