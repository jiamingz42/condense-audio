#!/bin/zsh

# Usage
#   LINGQ_APIKEY="blah" ./upload.zsh folder/to/subtitle course_id
#   LINGQ_APIKEY="blah" ./upload.zsh folder/to/subtitle course_id --dry-run
#
# `course_id` is a 6-digits integer (e.g. 686711)
#
# Optional Parameter
#   UL_LIMIT
#   UL_SKIP

function skip() {
  tail -n +"$1" | head -"$2"
}
function filter() {
  # Use prefix "UL_" to avoid name collision
  if [[ ! -z "$UL_LIMIT" && ! -z "$UL_SKIP" ]]; then
    skip "$UL_SKIP" "$UL_LIMIT"
  elif [[ ! -z "$UL_LIMIT" ]]; then
    head -"$UL_LIMIT"
  elif [[ ! -z "$UL_SKIP" ]]; then
    tail -n +"$UL_SKIP"
  else
    cat # pass-throught
  fi
}

if [ -z "$LINGQ_APIKEY" ]; then
  echo "Environment variable LINGQ_APIKEY not set"
  exit 1
fi

if [ -z "$1" ]; then
  echo "Folder not specified"
  exit 1
fi
SUBTITLE_DIR="$1"
shift

if [ -z "$1" ]; then
  echo "Course ID (6-digits integer) not specified"
  exit 1
fi
COURSE_ID="$1"
shift

# Certain WebVTT contains zero contents
fd vtt "$SUBTITLE_DIR" |
  sort |
  filter |
  while read line; do
    vtt="${line:a}"
    audio="${vtt:s/vtt/mp3}"
    title="${vtt:r:t}"

    # Echo Log Message
    echo ""
    echo "[INFO] Uploading $title"
    echo "[INFO]   file = ${vtt}"
    echo "[INFO]   audio = ${audio}"

    if [ "$1" = "--dry-run" ]; then
      continue
    fi

    curl -XPOST \
      -b "wwwlingqcomsa=4tp08bcoifioo4ukhxkcculuznsbijb7" \
      -b "csrftoken=" \
      -H "Authorization: Token $LINGQ_APIKEY" \
      -F "filename=${vtt:t}" \
      -F "title=${title}" \
      -F "file=@${vtt}" \
      -F "audio=@${audio}" \
      -F "status=private" \
      -F "save=true" \
      -F "collection=${COURSE_ID}" \
      https://www.lingq.com/api/v2/ja/lessons/import/
    sleep 2
  done
