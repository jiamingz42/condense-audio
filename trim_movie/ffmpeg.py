"""
Python wrapper for cli `ffmpeg` command
"""

from subprocess import *
from typing import Iterable, Tuple

import shlex


def cut_out_video(infile: str, outfile: str, start_time, duration) -> None:
    cmd = f"ffmpeg -hide_banner -loglevel error -i '{infile}' -ss {start_time} -t {duration} -c:a copy -map 0:1 -y '{outfile}'"
    _run_command(cmd)


def concat_audio_segments(list_file: str, outfile: str, files_count: int) -> None:
    cmd = ("ffmpeg -hide_banner -loglevel debug -safe 0 -f concat " +
           f"-segment_time_metadata 1 -i {list_file} " +
           "-vf select=concatdec_select " +
           f"-af aselect=concatdec_select,aresample=async=1 -y '{outfile}'")
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        for idx, line in _readlines_with_idx(proc.stdout):
            print(f'>{idx:03d}< {line}')
            continue


def get_duration(infile: str) -> float:
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{infile}'"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        if not proc.stdout:
            return 0
        stdout = proc.stdout.read().decode("utf-8").strip()
        if not stdout:
            raise ValueError("No stdout")
        return float(stdout)


def _readlines_with_idx(stream) -> Iterable[Tuple[int, str]]:
    for idx, line in enumerate(readlines(stream)):
        yield (idx, line)


def _run_command(cmd: str) -> None:
    with Popen(shlex.split(cmd), stdout=PIPE) as proc:
        if not proc.stdout:
            return
        stdout = proc.stdout.read()
        if stdout:
            print(stdout)


def _readlines(stream) -> Iterable[str]:
    while True:
        line = stream.readline().decode('utf-8')
        if line:
            yield line.strip()
        else:
            break
