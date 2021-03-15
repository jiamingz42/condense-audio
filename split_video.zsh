#!/bin/zsh

# This script first combine video (mp4) with its subtitle (vtt) into mkv file.
# Then it split it into multiple parts. Last, it extracts mp3 and subtitle from
# this splitted mkv files.

# Usage
#   ./split_video.zsh "雙層公寓：東京 2019-2020_S01E01_重返東京.mp4"

# Constant
MAX_DURATION=600 # seconds


VIDEO_FILE="$1"

pattern="$(echo $VIDEO_FILE | sed -E "s/.*(S[0-9]+E[0-9]+).*/\1/")"

SUBTITLE_FILE="$(ls *$pattern*vtt)"

merged_file="${VIDEO_FILE:r}_tmp.mkv"

mkvmerge -o "$merged_file" "$VIDEO_FILE" --language 0:ja "$SUBTITLE_FILE" | sed "s/^/[${pattern}] /"

split_file="${VIDEO_FILE:h}/split/${VIDEO_FILE:t:r}P.mkv"
mkvmerge -o $split_file --split 600s "$merged_file" | sed "s/^/[${pattern}] /"

rm "$merged_file"

# Example Output
#   File 'out-split-001.mkv': container: Matroska
#   Track ID 0: video (MPEG-4p10/AVC/H.264)
#   Track ID 1: audio (AAC)
#   Track ID 2: audio (AAC)
#   Track ID 3: subtitles (VobSub)
#   Track ID 4: subtitles (WebVTT)
#   Attachment ID 1: type 'image/jpeg', size 12967 bytes, file name 'cover.jpg'
# mkvmerge -i out-split-001.mkv

ls split/*.mkv | while read filename; do
  mkvextract tracks "$filename" "2:${filename:r}.mp3" | sed "s/^/[${pattern}] /"
  mkvextract tracks "$filename" "4:${filename:r}.vtt" | sed "s/^/[${pattern}] /"
  rm "$filename"
done

