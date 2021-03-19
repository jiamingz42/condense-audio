from tqdm import tqdm
from trim_movie.ffmpeg import concat_audio_segments, get_duration, cut_out_video
from trim_movie.subtitle import create_adjusted_subtile, group_captions, load_captions, AnyCaption
from trim_movie.type import *
from typing import Any, Callable, List
from termcolor import cprint

import os


# TODO: [P0] Can run in parallel
class AudioCondenser(object):
    def __init__(
            self,
            input_files: InputFiles,
            output_files: OutputFiles,
            config: Configuration,
            is_valid_subtitle: Callable[[str, AnyCaption], bool],
            map_subtile: Callable[[Any], Any]):
        self.input_files = input_files
        self.output_files = output_files
        self.config = config
        self.is_valid_subtitle = is_valid_subtitle
        self.map_subtile = map_subtile
        self.outfiles: List[IntermediateOutfile] = []

    def __enter__(self) -> "AudioCondenser":
        return self

    def __exit__(self, type, value, traceback) -> None:
        try:
            os.remove(self.config.list_file_path)
        except FileNotFoundError:
            pass
        if not self.config.keep_tmpdir:
            for outfile in self.outfiles:
                os.remove(outfile.path)

    def run(self) -> None:
        # Shorten Variable Name
        input_files = self.input_files
        output_files = self.output_files
        config = self.config
        outfiles = self.outfiles
        is_valid_subtitle = self.is_valid_subtitle
        map_subtile = self.map_subtile

        captions = load_captions(input_files.subtitle_path, is_valid_subtitle, map_subtile)
        if config.print_subtitle:
            for i, caption in enumerate(captions):
                print("%3d %s" % (i, caption.text))
            return

        groups = group_captions(captions, 1000)
        if len(groups) == 0:
            cprint("[WARNING] No content from subtitle. Will terminate early.", 'red')
            return

        # TODO: Map (input_files, groups) -> (video_path : str, intermediate_outfile : str, start : str, duration : str)
        print("Creating audio segments based on the subtitle ...")
        audio_ext = config.intermediate_audio_ext
        for i, group in enumerate(tqdm(groups)):
            intermediate_outfile = os.path.abspath(f"{config.tmpdir}/out_{i:03d}.{audio_ext}")
            cut_out_video(
                input_files.video_path,
                intermediate_outfile,
                str(group.start),
                str(group.duration),
            )
            outfiles.append(IntermediateOutfile(intermediate_outfile, group.duration))

        self.write_to_list_file()

        # TODO: Progress bar?
        print("Concating %d audio segments ..." % len(self.outfiles))
        concat_audio_segments(config.list_file_path, output_files.audio_path, len(self.outfiles))

        # TODO: Put it into a helper method
        group_durations = [
            *map(lambda group: group.duration, groups)]
        group_durations_acc = []
        for i, group_duration in enumerate(group_durations):
            if i == 0:
                group_durations_acc.append(group_duration)
            else:
                group_durations_acc.append(
                    group_durations_acc[-1] + group_duration)
        assert len(group_durations_acc) == len(group_durations)

        vtt = create_adjusted_subtile(groups)
        vtt.save(output_files.subtitle_path)

        self.print_duration_percent()

    def write_to_list_file(self) -> None:
        with open(self.config.list_file_path, "w") as list_txt:
            for f in self.outfiles:
                list_txt.write(f"file '{f.path}'\n")
                list_txt.write(f"duration {f.duration.total_seconds}\n")

    def print_duration_percent(self):
        video_in_duration = get_duration(self.input_files.video_path)
        outfile_duration = get_duration(self.output_files.audio_path)
        duration_percent = outfile_duration / video_in_duration * 100
        print(f"Output duration is {duration_percent:.2f} of the original")


class Builder(object):
    def __init__(self):
        self.input_files = None
        self.output_files = None
        self.config = None
        self.is_valid_subtitle = None
        self.map_subtile = None

    def setInputFiles(self, input_files: InputFiles):
        self.input_files = input_files
        return self

    def setOutputFiles(self, output_files: OutputFiles):
        self.output_files = output_files
        return self

    def setConfiguration(self, config: Configuration):
        self.config = config
        return self

    def setIsValidSubtitleFunc(self, is_valid_subtitle: Callable[[str, AnyCaption], bool]):
        self.is_valid_subtitle = is_valid_subtitle
        return self

    def setMapSubtitleFunc(self, map_subtile: Callable[[Any], Any]):
        self.map_subtile = map_subtile
        return self

    def build(self) -> AudioCondenser:
        assert self.input_files is not None
        assert self.output_files is not None
        assert self.config is not None
        assert self.is_valid_subtitle is not None
        assert self.map_subtile is not None
        return AudioCondenser(
            self.input_files,
            self.output_files,
            self.config,
            self.is_valid_subtitle,
            self.map_subtile)
