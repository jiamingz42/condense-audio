from tying import Union, Match

import os
import sys


def get_subtitle_outfile(origin_sub_out: str, match: Union[Match, None], video_infile: str) -> str:
    if origin_sub_out:
        return os.path.abspath(origin_sub_out)
    # TODO: Check `match.groups()` has at least one item
    elif match:
        subtitle_filename = '{idx}.vtt'.format(idx=match.group(1).strip())
        return os.path.join(os.path.dirname(video_infile), 'condensed', subtitle_filename)
    else:
        raise ValueError("Did not specify input subtitle `--sin`. Can't infer from input video `--vin` either.")


def get_audio_outfile(origin_audio_out: str, match: Union[Match, None], video_infile: str) -> str:
   if origin_audio_out:
        return os.path.abspath(origin_audio_out)
   elif match:
       final_outfile_name = '{idx}.mp3'.format(idx=match.group(1))
       return os.path.join(os.path.dirname(video_infile), 'condensed', final_outfile_name)
   else:
       raise ValueError("Did not specify output audio `--out`. Can't infer from input video `--vin` either.")
