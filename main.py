#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import *
from typing import NamedTuple, List
from tqdm import tqdm
from trim_movie.timestamp import Timestamp
from trim_movie.ffmpeg import concat_video, get_duration, cut_out_video
from trim_movie.subtitle import Caption, read_webvtt, group_captions, create_adjusted_subtile, load_captions
from glob import glob


import argparse
import math
import os
import re
import shlex
import webvtt


class Outfile(NamedTuple):
    path: str
    duration: Timestamp


def main() -> int:
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--vin', required=True,
                        dest='video_in', help='Video infile')
    parser.add_argument('--out', help='Outfile')
    parser.add_argument('--sin', dest='sub_in',
                        help='Subtitle infile. If not present, infer from `video_in`. For example, if `video_in` is /path/to/foo.mp4, then this field will be /path/to/foo.vtt')
    parser.add_argument('--sout', dest='sub_out', help='Subtitle outfile.')
    parser.add_argument('--tmpdir', default="/tmp/lingq")
    parser.add_argument('--keep-tmpdir', default=False, action='store_true')

    args = parser.parse_args()

    tmpdir = args.tmpdir
    keep_tmpdir = args.keep_tmpdir
    video_infile = os.path.abspath(args.video_in)

    if args.sub_in:
        subtitle_infile = os.path.abspath(args.sub_in)
    else:
        # Infer from `video_infile`
        # For example, `video_infile` = "雙層公寓：東京 2019-2020_S01E01_重返東京.mp4"
        #                                                       ******
        #  we will try to find subtitle in the same directory matching `*S01E01*.vtt`
        # TODO: Extract to a helper method (video_infile -> subtitle_infile)
        match = re.match(".*(S\d+E\d+)", video_infile)
        assert match is not None, "Did not specify `--sin`. Can't infer from `--vin` either."
        pattern = os.path.join(os.path.dirname(
            video_infile), "*{pattern}*.vtt".format(pattern=match.group(1)))
        file_matches = glob(pattern)
        assert len(
            file_matches) == 1, "len(file_matches) is not 1. file_matches = %s" % file_matches
        subtitle_infile = file_matches[0]

    if args.sub_out:
        subtitle_outfile = os.path.abspath(args.sub_out)
    else:
        match = re.match(".*(S\d+E\d+)", video_infile)
        assert match is not None, "Did not specify `--sin`. Can't infer from `--sout` either."
        subtitle_filename = '{idx}.vtt'.format(idx=match.group(1))
        subtitle_outfile = os.path.join(os.path.dirname(
            video_infile), 'condensed', subtitle_filename)

    if args.sub_out:
        final_outfile = os.path.abspath(args.out)
    else:
        match = re.match(".*(S\d+E\d+)", video_infile)
        assert match is not None, "Did not specify `--sin`. Can't infer from `--sout` either."
        final_outfile_name = '{idx}.mp3'.format(idx=match.group(1))
        final_outfile = os.path.join(os.path.dirname(
            video_infile), 'condensed', final_outfile_name)

    final_outfile_dir = os.path.dirname(final_outfile)
    list_file_path = os.path.join(tmpdir, "list.txt")

    assert os.path.isfile(video_infile), "File %s not found" % subtitle_infile
    assert os.path.isfile(
        subtitle_infile), "File %s not found" % subtitle_infile
    assert os.path.isdir(tmpdir), "Folder %s not found" % tmpdir

    # Make sure the dir for outfile exists
    if not os.path.exists(final_outfile_dir):
        os.makedirs(final_outfile_dir)

    print("Running with the following parameters:\n" +
          'Input\n' +
          '  Video = "%s"\n' % video_infile +
          '  Sub = "%s"\n' % subtitle_infile +
          'Output\n' +
          '  Audio = "%s"\n' % final_outfile +
          '  Sub = "%s"\n' % subtitle_outfile)

    outfiles : List[Outfile] = []  # will be mutated
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


def create_condense_audio(tmpdir: str, subtitle_infile: str, subtitle_outfile: str, video_infile: str, final_outfile: str, list_file_path: str, outfiles: List[Outfile]):
    # Step 1: Read, filter and map subtitle
    def is_valid_subtitle(caption: webvtt.Caption):
        if '♪' in caption.text:
            return False
        if (caption.end - caption.start).total_milliseconds < 0:
            raise ValueError("Invalid capton")
        return True

    def map_subtile(caption: webvtt.Caption):
        new_text = re.sub("\(.+\)", "", caption.text)
        if new_text == caption.text:
            return caption
        return Caption(caption.start, caption.end, new_text)


    captions = load_captions(subtitle_infile, is_valid_subtitle, map_subtile)
    # captions = [
    #     *map(map_subtile, filter(is_valid_subtitle, read_webvtt(subtitle_infile)))]

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
        for f in outfiles:
            list_txt.write(f"file '{f.path}'\n")
            list_txt.write(f"duration {f.duration.total_seconds}\n")

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
