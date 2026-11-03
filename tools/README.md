# Day 1 Kokoro audio generation

Current status: generator and page upgrade are prepared. Model inference and MP3
creation are not yet verified: this cloud environment's proxy denies Hugging Face
with HTTP 403. Existing production `index.html` is intentionally unchanged.

Run on a machine with Python 3.12, FFmpeg (including libmp3lame), and access to
Hugging Face model downloads:

```sh
python3 -m venv /tmp/english365-kokoro
/tmp/english365-kokoro/bin/pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
/tmp/english365-kokoro/bin/pip install -r tools/requirements-kokoro.txt
/tmp/english365-kokoro/bin/python tools/generate_day1.py
```

The generator runs `hexgrad/Kokoro-82M`, American English, `af_heart`, at 1.0 and
0.75 speed. Slow audio is synthesized at that speed, not time-stretched. It stages
all six files, validates MP3 codec, size, duration, decoded sample energy and finite
samples, and checks slow versions are longer. Only then does it copy the MP3s into
`audio/`, write `audio/validation.json`, and add eight controls to the existing
lesson (the word and Hello example share two files). Existing audio is never
silently overwritten. Failures exit nonzero; do not deploy after a failed run.

The page uses a single native audio element, synchronous user-initiated play,
large wrapping buttons, live playback/error status, and relative audio paths.
No browser speech synthesis, autoplay, paid API, or external runtime service.
`validation.json` records technical checks, not listening verification.

Fallback: upload `notebooks/Day1_Kokoro.ipynb` to Google Colab and Run all.
It embeds the current lesson and scripts, generates the same six files, provides
listening controls, and exports an HTML/audio ZIP. This notebook has syntax checks
but has not been run in a real Colab session.

Before publishing, listen to all files and verify served HTML and MP3 responses
(200, audio/mpeg), then test iPhone Safari, Android Chrome and WeChat: all eight
buttons, rapid switching without overlapping audio, repeated playback, visible
network errors and readable portrait layout. No physical-device test is claimed.
