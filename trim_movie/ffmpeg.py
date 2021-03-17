"""
Python wrapper for cli `ffmpeg` command
"""

from subprocess import *
from typing import Iterable

import shlex

def run_command(cmd: str) -> None:
    with Popen(shlex.split(cmd), stdout=PIPE) as proc:
        if not proc.stdout:
            return
        stdout = proc.stdout.read()
        if stdout:
            print(stdout)


def cut_out_video(infile: str, outfile: str, start_time, duration) -> None:
    cmd = f"ffmpeg -hide_banner -loglevel error -i '{infile}' -ss {start_time} -t {duration} -c:a copy -map 0:1 -y '{outfile}'"
    run_command(cmd)


def concat_video(infile: str, outfile: str) -> None:
    cmd = f"ffmpeg -hide_banner -loglevel error -safe 0 -f concat -segment_time_metadata 1 -i {infile} -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 -y '{outfile}'"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        for i, line in enumerate(readlines(proc.stdout)):
            #print(i, line[:-1])
            continue


def readlines(stream) -> Iterable[str]:
    while True:
        line = stream.readline().decode('utf-8')
        if line:
            yield line
        else:
            break


def get_duration(infile: str) -> float:
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{infile}'"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        if not proc.stdout:
            return 0
        stdout = proc.stdout.read().decode("utf-8").strip()
        if not stdout:
            raise ValueError("No stdout")
        return float(stdout)
