from tying import Union, Match

import os
import sys

def get_subtitle_outfile(origin_sub_out: str, match: Union[Match,None], video_infile: str) -> str:
    if origin_sub_out:
        return os.path.abspath(origin_sub_out)
    # TODO: Check `match.groups()` has at least one item
    elif match:
        subtitle_filename = '{idx}.vtt'.format(idx=match.group(1).strip())
        return os.path.join(os.path.dirname(video_infile), 'condensed', subtitle_filename)
    else:
        assert match is not None, "Did not specify `--sin`. Can't infer from `--vin` either."
        sys.exit(1)
