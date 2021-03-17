#!/usr/bin/python
# -*- coding: utf-8 -*-

from glob import glob
from subprocess import *
from trim_movie.subtitle import Caption
from trim_movie.type import *
from trim_movie import condenser
from typing import Union, List


import argparse
import ass
import os
import re
import webvtt


def get_files(patterns: List[str]) -> List[str]:
    file_matches = []
    for pattern in patterns:
        file_matches += glob(pattern)
    return file_matches


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
    parser.add_argument(
        '--print-subtitle',
        default=False,
        action='store_true',
        help='If true, only print filtered / processed subtitle w/o processing the video')

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
        pattern = match.group(1)
        file_matches = get_files([
            os.path.join(os.path.dirname(video_infile),
                         "*{pattern}*.vtt".format(pattern=pattern)),
            os.path.join(os.path.dirname(video_infile),
                         "*{pattern}*.ass".format(pattern=pattern))
        ])
        assert len(
            file_matches) == 1, "len(file_matches) is not 1. pattern = %s. file_matches = %s" % (pattern, file_matches)

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

    audioCondenser: condenser.AudioCondenser = condenser.Builder()\
        .setInputFiles(InputFiles(video_infile, subtitle_infile))\
        .setOutputFiles(OutputFiles(final_outfile, subtitle_outfile))\
        .setConfiguration(Configuration(args.print_subtitle, list_file_path, tmpdir,  keep_tmpdir))\
        .setIsValidSubtitleFunc(is_valid_subtitle)\
        .setMapSubtitleFunc(map_subtile)\
        .build()

    with audioCondenser as c:
        c.run()

    return 0


# TODO: Provide these function via extension
def is_valid_subtitle(
        filename: str,
        caption: Union[webvtt.Caption, ass.line.Dialogue]) -> bool:
    if filename.endswith(".vtt"):
        if '♪' in caption.text:
            return False
        if (caption.end - caption.start).total_milliseconds < 0:
            raise ValueError("Invalid capton: %s" % str(caption))
        return True
    elif filename.endswith(".ass"):
        # TODO: Hardcoded - won't work for another *.ass file
        return caption.style == '*Default-ja'
    else:
        raise ValueError("Invalid subtitle: %s" % filename)


def map_subtile(caption: webvtt.Caption) -> webvtt.Caption:
    new_text = re.sub("\(.+\)", "", caption.text)
    if new_text == caption.text:
        return caption
    return Caption(caption.start, caption.end, new_text)


if __name__ == '__main__':
    main()
