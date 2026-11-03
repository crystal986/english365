"""Run real Kokoro inference, validate all six MP3s, then enable page controls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile

TEXTS = {'hello': 'Hello!', 'hello_mary': 'Hello, Mary!', 'hello_everyone': 'Hello, everyone!'}
SPEEDS = {'normal': 1.0, 'slow': 0.75}


def validate(path):
    import numpy as np
    info = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    stream = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                   '-f', 'f32le', '-ac', '1', '-ar', '24000', '-'])
    samples = np.frombuffer(raw, dtype='<f4')
    rms = float(np.sqrt(np.mean(samples ** 2)))
    peak = float(np.max(np.abs(samples))) if len(samples) else 0
    duration = float(info['format']['duration'])
    if not (stream['codec_name'] == 'mp3' and path.stat().st_size > 1000
            and 0.2 < duration < 20 and np.isfinite(samples).all()
            and math.isfinite(rms) and rms > 0.001 and peak > 0.01):
        raise ValueError(f'Invalid or silent audio: {path}')
    return dict(bytes=path.stat().st_size, duration_seconds=duration,
                codec=stream['codec_name'], sample_rate=int(stream['sample_rate']),
                rms=rms, peak=peak, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    original = (root / 'index.html').read_text(encoding='utf-8')
    if 'id="day1-player"' in original:
        raise SystemExit('Page already has audio controls; inspect before regenerating.')
    # Check the expected page before downloading a model or writing any output.
    for text in TEXTS.values():
        if f'<div class="english">{text}</div>' not in original:
            raise SystemExit(f'Expected lesson text missing: {text}')
    import numpy as np
    import soundfile as sf
    import torch
    from kokoro import KPipeline
    torch.set_num_threads(min(4, torch.get_num_threads()))
    pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M', device='cpu')
    report = {'model': 'hexgrad/Kokoro-82M', 'voice': 'af_heart',
              'speeds': SPEEDS, 'method': 'Kokoro inference; no time stretching',
              'listening_verified': False, 'files': {}}
    # Stage outside the repository: no buttons or audio are published on failure.
    with tempfile.TemporaryDirectory(prefix='english365-kokoro-') as tmp:
        staging = Path(tmp)
        for key, text in TEXTS.items():
            for label, speed in SPEEDS.items():
                chunks = [audio.detach().cpu().numpy() for _, _, audio in
                          pipeline(text, voice='af_heart', speed=speed) if audio is not None]
                if not chunks:
                    raise RuntimeError(f'Kokoro returned no audio: {text}')
                waveform = np.concatenate(chunks)
                wav = staging / f'{key}_{label}.wav'
                mp3 = staging / f'{key}_{label}.mp3'
                sf.write(wav, waveform, 24000, subtype='PCM_16')
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-i', str(wav),
                                '-codec:a', 'libmp3lame', '-b:a', '128k', str(mp3)], check=True)
                report['files'][mp3.name] = dict(text=text, speed=speed, **validate(mp3))
                print(mp3.name, report['files'][mp3.name], flush=True)
        for key in TEXTS:
            if report['files'][key+'_slow.mp3']['duration_seconds'] <= report['files'][key+'_normal.mp3']['duration_seconds']:
                raise RuntimeError(f'Slow audio is not longer: {key}')
        from upgrade_page import upgrade
        updated = upgrade(original)
        (root / 'audio').mkdir(exist_ok=True)
        for mp3 in staging.glob('*.mp3'):
            dest = root / 'audio' / mp3.name
            if dest.exists():
                raise FileExistsError(f'Refusing to overwrite {dest}')
        for mp3 in staging.glob('*.mp3'):
            (root / 'audio' / mp3.name).write_bytes(mp3.read_bytes())
        (root / 'audio' / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        (root / 'index.html').write_text(updated, encoding='utf-8')
    print('Six MP3s validated and HTML upgraded. Listening and browser/device checks remain required.')


if __name__ == '__main__':
    main()
