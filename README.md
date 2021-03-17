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
```
PYTHONPATH=. python tests/*.py
```

# Formating

```
fd py -X autoflake --in-place --remove-unused-variables --remove-all-unused-imports
```
