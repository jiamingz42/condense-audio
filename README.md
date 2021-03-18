# Motivation

LingQ allows user to upload subtitle (e.g. srt, ass, vtt) along with audio as a
lesson. Then user can read the subtitle sentence by sentence and can also
choose to play the audio for this sentence.

User can also listen to this audio for passive learning. To increase the
efficient, I created this program to only extract those audio segments where
there are conversations. There are similiar programs that can extract condensed
audio but it doesn't adjust the subtitle accordingly. This program does both.


# Usage

```bash
python main.py --sin sample.vtt --sout out.vtt --vin sample.mp4 --out combined.mp3 --keep-tmpdir
```

# Test

Check if all the code conforms to the type hinting

```
fd py -X mypy
```

Run all tests

`pytest` gives out more readable error than the vanilla unittest module

```
PYTHONPATH=. $(pyenv which pytest)
```

# Formating

```
fd py -X autoflake --in-place --remove-unused-variables --remove-all-unused-imports
```

# TODO

1. Can post translation to LingQ
2. Can exapnd the caption endtime 
3. Can join short caption
