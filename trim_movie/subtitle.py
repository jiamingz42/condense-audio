from trim_movie.timestamp import Timestamp
from typing import NamedTuple, List, Callable, Iterator, Any

import ass
import webvtt


class Caption(NamedTuple):
    start: Timestamp
    end: Timestamp
    text: str


# TODO: map_subtitle -> Generic type?
def load_captions(subtitle_infile: str,
                  is_valid_subtitle: Callable[[str, Any], bool],
                  map_subtile: Callable[[Any], Any]) -> List[Caption]:
    if subtitle_infile.endswith(".vtt"):
        return [*map(map_subtile, read_webvtt(subtitle_infile, is_valid_subtitle))]
    elif subtitle_infile.endswith(".ass"):
        return [*read_ass(subtitle_infile, is_valid_subtitle)]
    else:
        raise ValueError("Unsupported subtitle type: %s" % subtitle_infile)


def read_webvtt(infile: str,
                is_valid_subtitle: Callable[[str, webvtt.Caption], bool]
                ) -> Iterator[Caption]:
    for caption in webvtt.read(infile):
        if is_valid_subtitle(infile, caption):
            yield Caption(
                Timestamp.from_s(caption.start),
                Timestamp.from_s(caption.end),
                caption.text
            )


def read_ass(infile: str,
             is_valid_subtitle: Callable[[str, ass.line.Dialogue], bool]
             ) -> Iterator[Caption]:
    with open(infile, "r") as f:
        ass_subtitle = ass.parse(f)
    for event in ass_subtitle.events:
        if is_valid_subtitle(infile, event):
            yield Caption(
                Timestamp.from_timedelta(event.start),
                Timestamp.from_timedelta(event.end),
                event.text
            )


def group_captions(captions: List[Caption], interval: int) -> List[List[Caption]]:
    groups: List[List[Caption]] = [[]]
    for i, caption in enumerate(captions):
        if i > 0 and (caption.start - captions[i - 1].end).total_milliseconds > interval:
            groups.append([])
        groups[-1].append(caption)
    return groups


def create_adjusted_subtile(groups: List[List[Caption]]) -> webvtt.WebVTT:
    vtt = webvtt.WebVTT()
    for i, group in enumerate(groups):
        if i == 0:
            shift = group[0].start
        else:
            last_timestamp = Timestamp.from_s(vtt.captions[-1].end)
            shift = (group[0].start - last_timestamp).map(lambda x: x - 1)

        for caption in group:
            caption = webvtt.Caption(
                str(caption.start - shift),
                str(caption.end - shift),
                caption.text
            )
            vtt.captions.append(caption)
    return vtt
