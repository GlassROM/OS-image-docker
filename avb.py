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

def calculate_num_data_blocks(image_size, data_block_size):
    return image_size // data_block_size

def calculate_hash_start_block(num_data_blocks):
    # Assuming the hash tree starts immediately after the data blocks
    return num_data_blocks

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
    verity_version_str = hashtree_descriptor['Version of dm-verity']

    image_size = int(image_size_str.split()[0].replace(',', ''))
    data_block_size = int(data_block_size_str.split()[0])
    hash_block_size = int(hash_block_size_str.split()[0])
    verity_version = int(verity_version_str.strip())

    hash_algorithm = hashtree_descriptor['Hash Algorithm']
    root_digest = hashtree_descriptor['Root Digest']
    salt = hashtree_descriptor['Salt']
    fec_params = calculate_fec_params(hashtree_descriptor)
    target_length = calculate_target_length(image_size)
    num_data_blocks = calculate_num_data_blocks(image_size, data_block_size)
    hash_start_block = calculate_hash_start_block(num_data_blocks)
    data_device = f'PARTUUID={partuuid}'
    hash_device = data_device  # Assuming data and hash are on the same device

    # Build the mapping table
    mapping_table = f"0 {target_length} verity {verity_version} {data_device} {hash_device} {data_block_size} {hash_block_size} {num_data_blocks} {hash_start_block} {hash_algorithm} {root_digest} {salt}"

    # Initialize optional parameters list
    optional_params = []

    # Add error behavior options
    optional_params.extend(['restart_on_corruption', 'ignore_zero_blocks', 'try_verify_in_tasklet'])

    if fec_params:
        # Include FEC parameters
        optional_params.extend([
            'use_fec_from_device', data_device,
            'fec_roots', str(fec_params['fec_roots']),
            'fec_blocks', str(fec_params['fec_blocks']),
            'fec_start', str(fec_params['fec_start_block'])
        ])

    # Calculate the number of optional parameters
    num_optional_params = len(optional_params)

    # Add the number of optional parameters and the optional parameters to the mapping table
    mapping_table += f" {num_optional_params} " + ' '.join(optional_params)

    # Build the dm parameter
    dm_param = f'dm="1 vroot none ro 1,{mapping_table}"'

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
