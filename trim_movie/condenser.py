from tqdm import tqdm
from trim_movie.ffmpeg import concat_video, get_duration, cut_out_video
from trim_movie.type import *
from trim_movie.subtitle import create_adjusted_subtile, group_captions, load_captions
from typing import List

import os


class AudioCondenser(object):
    # TODO: Type hinting
    def __init__(self,
                 input_files: InputFiles,
                 output_files: OutputFiles,
                 config: Configuration,
                 is_valid_subtitle,
                 map_subtile):
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
        return self.create_condense_audio(
            self.input_files,
            self.output_files,
            self.config,
            self.outfiles,
            self.is_valid_subtitle,
            self.map_subtile)

    @staticmethod
    def create_condense_audio(input_files: InputFiles,
                              output_files: OutputFiles,
                              config: Configuration,
                              outfiles: List[IntermediateOutfile],
                              is_valid_subtitle,
                              map_subtile) -> None:
        captions = load_captions(input_files.subtitle_path,
                                 is_valid_subtitle, map_subtile)
        if config.print_subtitle:
            for i, caption in enumerate(captions):
                print("%3d %s" % (i, caption.text))
            return

        groups = group_captions(captions, 1000)

        print("Creating audio segments based on the subtitle ...")
        for i, group in enumerate(tqdm(groups)):
            start, end = group[0].start, group[-1].end
            duration = end - start
            outfile = os.path.abspath("%s/out_%03d.aac" % (config.tmpdir, i))
            cut_out_video(
                input_files.video_path,
                outfile,
                str(start),
                str(duration),
            )
            outfiles.append(IntermediateOutfile(outfile, duration))

        with open(config.list_file_path, "w") as list_txt:
            for f in outfiles:
                list_txt.write(f"file '{f.path}'\n")
                list_txt.write(f"duration {f.duration.total_seconds}\n")

        # TODO: Progress bar?
        print("Concating audio segments ...")
        concat_video(config.list_file_path, output_files.audio_path)

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
        vtt.save(output_files.subtitle_path)

        video_in_duration = get_duration(input_files.video_path)
        outfile_duration = get_duration(output_files.audio_path)
        print(f"Output duration is %.2f%% of the original" %
              (outfile_duration / video_in_duration * 100))


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

    def setIsValidSubtitleFunc(self, is_valid_subtitle):
        self.is_valid_subtitle = is_valid_subtitle
        return self

    def setMapSubtitleFunc(self, map_subtile):
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
