#!/usr/bin/env python3

import os
import subprocess

def get_image_size(image_path):
    return os.path.getsize(image_path)

def get_max_image_size(partition_size):
    cmd = [
        'avbtool', 'add_hashtree_footer',
        '--calc_max_image_size',
        '--partition_size', str(partition_size)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running avbtool: {result.stderr}")
        return None
    # The output is a single line containing just the size
    try:
        max_image_size = int(result.stdout.strip())
        return max_image_size
    except ValueError:
        print(f"Unexpected output from avbtool: {result.stdout}")
        return None

def find_min_partition_size(image_size):
    # Initialize bounds for binary search
    lower_bound = image_size
    upper_bound = image_size * 2  # Arbitrary upper limit
    min_partition_size = upper_bound

    while lower_bound <= upper_bound:
        mid = (lower_bound + upper_bound) // 2
        max_image_size = get_max_image_size(mid)
        if max_image_size is None:
            print("Failed to get max_image_size from avbtool.")
            return None
        if max_image_size >= image_size:
            min_partition_size = mid
            upper_bound = mid - 1
        else:
            lower_bound = mid + 1

    return min_partition_size

def main():
    image_path = 'archlinux.img'
    image_size = get_image_size(image_path)
    print(f"Current image size: {image_size} bytes")
    min_partition_size = find_min_partition_size(image_size)
    if min_partition_size:
        print(f"Minimum partition size required: {min_partition_size} bytes")
        subprocess.run(["avbtool", "add_hashtree_footer", "--image", "archlinux.img", "--partition_size", str(min_partition_size), "--partition_name", "root", "--hash_algorithm", "blake2b-256"])
    else:
        print("Could not determine the minimum partition size.")

if __name__ == '__main__':
    main()
