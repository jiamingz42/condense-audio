#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import *
from typing import NamedTuple
from trim_movie.timestamp import Timestamp

import shlex
import webvtt
import os
import re
import math


def run_command(cmd):
    with Popen(shlex.split(cmd), stdout=PIPE) as proc:
        print(proc.stdout.read())


def cut_out_video(infile, outfile, start_time, duration):
    cmd = f"ffmpeg -i \"{infile}\" -ss {start_time} -t {duration} -c:a copy -map 0:1 -y \"{outfile}\""
    print(cmd)
    run_command(cmd)


def concat_video(infile, outfile):
    cmd = f"ffmpeg -safe 0 -f concat -segment_time_metadata 1 -i {infile} -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 -y {outfile}"
    run_command(cmd)


def get_duration(infile):
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {infile}"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        stdout = proc.stdout.read().decode("utf-8").strip()
        if not stdout:
            raise StandardError()
        return float(stdout)


class Caption(NamedTuple):
    start: Timestamp
    end: Timestamp
    text: str

# round to 0.5 percision, 00:12.22 vs 00:12:22.3


def read_webvtt(infile):
    for i, caption in enumerate(webvtt.read(infile)):
        if i == 47:
            print(caption)
            import ipdb; ipdb.set_trace()
        yield Caption(
            Timestamp.from_s(caption.start),
            Timestamp.from_s(caption.end),
            caption.text
        )


def main():
    # Step 1: Read, filter and map subtitle
    d = []
    captions = []
    for caption in read_webvtt('sample.vtt'):
        if '♪' in caption.text:
            continue
        captions.append(caption)
        if (caption.end - caption.start).total_milliseconds < 0:
            import ipdb; ipdb.set_trace()
        d.append((caption.end - caption.start).total_milliseconds)

    groups = [[]]
    for i, caption in enumerate(captions):
        if i > 0 and (caption.start - captions[i-1].end).total_milliseconds > 2000:
            groups.append([])
        groups[-1].append(caption)

    print(len(groups))
    print(sorted(d)[:5])

    return


    vtt = webvtt.WebVTT()

    TMP_DIR = "tmp"
    list_file_path = os.path.join(TMP_DIR, "list.txt")
    # caption.start, caption.end, caption.text
    total = Timestamp(0)
    t = 0
    with open(list_file_path, "w") as list_txt:
        for i, caption in enumerate(read_webvtt('sample.vtt')):
            expect_duration = caption.end - caption.start
            print(i, caption)

            outfile = "%s/out_%03d.aac" % (TMP_DIR, i)
            cut_out_video(
                "/Users/jiamingz/dev/trim_movie/sample.mp4",
                outfile,
                str(caption.start),
                str(expect_duration),
            )
            # duration = get_duration(outfile)
            duration = 0
            t += duration

            list_txt.write(f"file '{os.path.abspath(outfile)}'\n")
            # list_txt.write(f"file '/Users/jiamingz/dev/trim_movie/sample.mp4'\n")
            # list_txt.write(f"inpoint {caption['start'].total_milliseconds / 1000}\n")
            # list_txt.write(f"outpoint {caption['end'].total_milliseconds / 1000}\n")

            # out_duration = get_duration(outfile)
            total = total + expect_duration
            # total = total + out_duration
            # print(expect_duration, out_duration)

            if vtt.captions:
                shift = (
                    caption.start - Timestamp.from_s(vtt.captions[-1].end)).map(lambda x: x - 1)
            else:
                shift = caption.start

            caption = webvtt.Caption(
                str(caption.start - shift),
                str(caption.end - shift),
                caption.text
            )
            vtt.captions.append(caption)

    concat_video(list_file_path, os.path.join(TMP_DIR, "combine.mp4"))
    print(f"expect {total} {t}")

    actual = get_duration(os.path.join(TMP_DIR, "combine.mp4"))
    print(f"actual: {actual}")

    vtt.save('my_captions.vtt')



main()
