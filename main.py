#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import *
from typing import NamedTuple
from tqdm import tqdm
from trim_movie.timestamp import Timestamp


import argparse
import math
import os
import re
import shlex
import webvtt


def run_command(cmd):
    with Popen(shlex.split(cmd), stdout=PIPE) as proc:
        stdout = proc.stdout.read()
        if stdout:
            print(stdout)


def cut_out_video(infile, outfile, start_time, duration):
    cmd = f"ffmpeg -hide_banner -loglevel error -i '{infile}' -ss {start_time} -t {duration} -c:a copy -map 0:1 -y '{outfile}'"
    run_command(cmd)


def concat_video(infile, outfile):
    cmd = f"ffmpeg -hide_banner -loglevel error -safe 0 -f concat -segment_time_metadata 1 -i {infile} -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 -y '{outfile}'"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        for i, line in enumerate(readlines(proc.stdout)):
            #print(i, line[:-1])
            continue


def readlines(stream):
    while True:
        line = stream.readline().decode('utf-8')
        if line:
            yield line
        else:
            break


def get_duration(infile):
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{infile}'"
    with Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT) as proc:
        stdout = proc.stdout.read().decode("utf-8").strip()
        if not stdout:
            raise StandardError()
        return float(stdout)


class Caption(NamedTuple):
    start: Timestamp
    end: Timestamp
    text: str


class Outfile(NamedTuple):
    path: str
    duration: Timestamp


def read_webvtt(infile):
    for i, caption in enumerate(webvtt.read(infile)):
        yield Caption(
            Timestamp.from_s(caption.start),
            Timestamp.from_s(caption.end),
            caption.text
        )


def group_captions(captions, interval):
    groups = [[]]
    for i, caption in enumerate(captions):
        if i > 0 and (caption.start - captions[i - 1].end).total_milliseconds > interval:
            groups.append([])
        groups[-1].append(caption)
    return groups


def create_adjusted_subtile(groups):
    vtt = webvtt.WebVTT()
    for i, group in enumerate(groups):
        if i == 0:
            shift = group[0].start
        else:
            last_timestamp = Timestamp.from_s(vtt.captions[-1].end)
            shift = (group[0].start - last_timestamp).map(lambda x: x - 1)
            pass

        for caption in group:
            caption = webvtt.Caption(
                str(caption.start - shift),
                str(caption.end - shift),
                caption.text
            )
            vtt.captions.append(caption)
    return vtt


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--vin', required=True,
                        dest='video_in', help='Video infile')
    parser.add_argument('--out', required=True, help='Outfile')
    parser.add_argument('--sin', required=True,
                        dest='sub_in', help='Subtitle infile')
    parser.add_argument('--sout', required=True,
                        dest='sub_out', help='Subtitle infile')
    parser.add_argument('--tmpdir', default="tmp")
    parser.add_argument('--keep-tmpdir', default=False, action='store_true')

    args = parser.parse_args()

    tmpdir = args.tmpdir
    keep_tmpdir = args.keep_tmpdir
    subtitle_infile = os.path.abspath(args.sub_in)
    subtitle_outfile = os.path.abspath(args.sub_out)
    video_infile = os.path.abspath(args.video_in)
    final_outfile = os.path.abspath(args.out)
    final_outfile_dir = os.path.dirname(final_outfile)
    list_file_path = os.path.join(tmpdir, "list.txt")

    assert os.path.isfile(video_infile), "File %s not found" % subtitle_infile
    assert os.path.isfile(
        subtitle_infile), "File %s not found" % subtitle_infile
    assert os.path.isdir(tmpdir), "Folder %s not found" % tmpdir

    # Make sure the dir for outfile exists
    if not os.path.exists(final_outfile_dir):
        os.makedirs(final_outfile_dir)

    outfiles = []  # will be mutated
    try:
        create_condense_audio(tmpdir, subtitle_infile, subtitle_outfile,
                              video_infile, final_outfile, list_file_path, outfiles)
    finally:
        # Clean up
        try:
            os.remove(list_file_path)
        except FileNotFoundError:
            pass
        if not keep_tmpdir:
            for outfile in outfiles:
                os.remove(outfile.path)

    return 0


def create_condense_audio(tmpdir, subtitle_infile, subtitle_outfile, video_infile, final_outfile, list_file_path, outfiles):
    # Step 1: Read, filter and map subtitle
    def is_valid_subtitle(caption: webvtt.Caption):
        if '♪' in caption.text:
            return False
        if (caption.end - caption.start).total_milliseconds < 0:
            raise StandardError("Invalid capton")
        return True

    def map_subtile(caption: webvtt.Caption):
        new_text = re.sub("\(.+\)", "", caption.text)
        if new_text == caption.text:
            return caption
        return Caption(caption.start, caption.end, new_text)

    captions = [
        *map(map_subtile, filter(is_valid_subtitle, read_webvtt(subtitle_infile)))]

    groups = group_captions(captions, 1000)

    print("Creating audio segments based on the subtitle ...")
    for i, group in enumerate(tqdm(groups)):
        start, end = group[0].start, group[-1].end
        duration = end - start
        outfile = os.path.abspath("%s/out_%03d.aac" % (tmpdir, i))
        cut_out_video(
            video_infile,
            outfile,
            str(start),
            str(duration),
        )
        outfiles.append(Outfile(outfile, duration))

    with open(list_file_path, "w") as list_txt:
        for outfile in outfiles:
            list_txt.write(f"file '{outfile.path}'\n")
            list_txt.write(f"duration {outfile.duration.total_seconds}\n")

    print("Concating audio segments ...")
    concat_video(list_file_path, final_outfile)

    group_durations = [
        *map(lambda group: group[-1].end - group[0].start, groups)]
    group_durations_acc = []
    for i, group_duration in enumerate(group_durations):
        if i == 0:
            group_durations_acc.append(group_duration)
        else:
            group_durations_acc.append(
                group_durations_acc[-1] + group_duration)
    assert len(group_durations_acc) == len(group_durations)

    vtt = create_adjusted_subtile(groups)
    vtt.save(subtitle_outfile)

    video_in_duration = get_duration(video_infile)
    outfile_duration = get_duration(final_outfile)
    print(f"Output duration is %.2f%% of the original" %
          (outfile_duration / video_in_duration * 100))



if __name__ == '__main__':
  main()
