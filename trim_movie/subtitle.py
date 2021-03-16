from trim_movie.timestamp import Timestamp
from typing import NamedTuple, List

import webvtt

class Caption(NamedTuple):
    start: Timestamp
    end: Timestamp
    text: str

def load_captions(subtitle_infile: str, is_valid_subtitle, map_subtile) -> List[str]:
    return [*map(map_subtile, filter(is_valid_subtitle, read_webvtt(subtitle_infile)))]

def read_webvtt(infile: str):
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