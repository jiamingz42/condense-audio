from trim_movie.timestamp import Timestamp
from trim_movie.logger import log
from typing import NamedTuple, List, Callable, Iterator, Any, Union

import ass
import webvtt


class Caption(NamedTuple):
    start: Timestamp
    end: Timestamp
    text: str


class CaptionGroup(object):
    def __init__(self, caption: List[Caption] = None):
        self.captions: List[Caption] = [] if caption is None else caption

    def __str__(self):
        return f"CaptionGroup(captions={self.captions})>"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if type(other) != CaptionGroup:
            return False

        if len(self.captions) != len(other.captions):
            return False

        return all([c1 == c2 for c1, c2 in zip(self.captions, other.captions)])

    def append(self, caption: Caption):
        self.captions.append(caption)

    @property
    def start(self):
        assert len(self.captions) > 0
        return self.captions[0].start

    @property
    def end(self):
        assert len(self.captions) > 0
        return self.captions[-1].end

    @property
    def duration(self):
        assert len(self.captions) > 0
        return self.end - self.start

    @staticmethod
    def of(caption: Caption) -> "CaptionGroup":
        return CaptionGroup([caption])


AnyCaption = Union[webvtt.Caption, ass.line.Dialogue]


# TODO: map_subtitle -> Generic type?
def load_captions(subtitle_infile: str,
                  is_valid_subtitle: Callable[[str, AnyCaption], bool],
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
    with open(infile, "r", encoding='utf_8_sig') as f:
        ass_subtitle = ass.parse(f)
    total_count = valid_count = 0
    for event in ass_subtitle.events:
        total_count += 1
        if is_valid_subtitle(infile, event):
            valid_count += 1
            yield Caption(
                Timestamp.from_timedelta(event.start),
                Timestamp.from_timedelta(event.end),
                event.text
            )
    print(f"[INFO] {valid_count}/{total_count} subtitle lines are valid")


def group_captions(captions: List[Caption], interval: int) -> List[CaptionGroup]:
    if len(captions) == 0:
        return []

    groups: List[CaptionGroup] = [CaptionGroup([captions[0]])]
    for last_caption, caption in zip(captions, captions[1:]):
        if (caption.start - last_caption.end).total_milliseconds > interval:
            groups.append(CaptionGroup.of(caption))
        else:
            groups[-1].append(caption)
    return groups


def create_adjusted_subtile(groups: List[CaptionGroup]) -> webvtt.WebVTT:
    vtt = webvtt.WebVTT()
    for i, group in enumerate(groups):
        if i == 0:
            shift = group.start
        else:
            last_timestamp = Timestamp.from_s(vtt.captions[-1].end)
            shift = (group.start - last_timestamp).map(lambda x: x - 1)

        for caption in group.captions:
            adjusted_start = caption.start - shift
            adjusted_end = caption.end - shift
            if adjusted_start < Timestamp(0):
                log(f"[WARNING] Invalid adjusted timestamp for caption\n\t{caption}")
                continue
            vtt_caption = webvtt.Caption(
                str(adjusted_start),
                str(adjusted_end),
                caption.text
            )
            vtt.captions.append(vtt_caption)
    return vtt
