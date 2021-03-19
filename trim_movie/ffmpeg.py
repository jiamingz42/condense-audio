"""
Python wrapper for cli `ffmpeg` command
"""

from subprocess import PIPE, Popen, STDOUT
from typing import Iterable, Tuple, Union
from tqdm import tqdm

import shlex


def cut_out_video(infile: str, outfile: str, start_time, duration) -> None:
    cmd = f"ffmpeg -hide_banner -loglevel error -i '{infile}' -ss {start_time} -t {duration} -c:a copy -map 0:1 -y '{outfile}'"
    _run_command(cmd)


def concat_audio_segments(list_file: str, outfile: str, files_count: int) -> None:
    # NOTE: Need to set loglevel to debug to track the progress of concatenation
    cmd = ("ffmpeg -hide_banner -loglevel debug -safe 0 -f concat " +
           f"-segment_time_metadata 1 -i {list_file} " +
           "-vf select=concatdec_select " +
           f"-af aselect=concatdec_select,aresample=async=1 -y '{outfile}'")
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        progress = _ConcatProgress(files_count)
        for idx, line in _readlines_with_idx(proc.stdout):
            progress.update(line)


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
    for idx, line in enumerate(_readlines(stream)):
        yield (idx, line)


def _readlines(stream) -> Iterable[str]:
    while True:
        line = stream.readline().decode('utf-8')
        if line:
            yield line.strip()
        else:
            break


def _run_command(cmd: str) -> None:
    with Popen(shlex.split(cmd), stdout=PIPE) as proc:
        if not proc.stdout:
            return
        stdout = proc.stdout.read()
        if stdout:
            print(stdout)


class _ConcatProgress(object):
    def __init__(self, files_count: int):
        self.last_file_idx = -1
        self.pbar = tqdm(total=files_count)

    def update(self, line: str) -> None:
        file_idx = self._get_concat_file_idx(line)

        # `file_idx` could be 0 so should check against `None`
        if file_idx is None:
            return
        if self.last_file_idx != file_idx:
            self.last_file_idx = file_idx
            self.pbar.update(1)

    @staticmethod
    def _get_concat_file_idx(line: str) -> Union[None, int]:
        """
        Extract file index (in this case, 10) from a line as following
        `[concat @ 0x7fbfa0808200] file:10 stream:0 pts:16859136 pts_time:0.597333 dts:16859136 dts_time:0.597333 -> pts:1547164416 pts_time:54.8173 dts:1547164416 dts_time:54.8173`
        """
        if not ('[concat' in line and ' file:' in line):
            return None
        _, tail = line.split('] ')
        file_stat = tail.split(' ')[0]
        assert 'file:' in file_stat, f"Invalid format: {file_stat}\nFull Line: \"{line}\""
        return int(file_stat.split(":")[1])
