#!/bin/python

"""
Usage
"""

from glob import glob
import sys

assert len(sys.argv) == 3, f"sys.argv = {sys.argv}"

video_dir = sys.argv[1]
sub_dir = sys.argv[2]

for video_name, sub_name in zip(glob(f"{video_dir}/*.mkv"), glob(f"{sub_dir}/*.ass")):
    sub_new_name = video_name.replace(".mkv", ".ass")
    print(f"cp \"{sub_name}\" \"{sub_new_name}\"")
