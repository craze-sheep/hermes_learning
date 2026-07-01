---
name: music-creation
description: "Music and audio: songwriting, AI generation (HeartMuLa, AudioCraft, Suno), audio analysis (spectrograms, MFCC)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Music, Audio, Generation, Songwriting, Suno, HeartMuLa, AudioCraft, Spectrogram, Analysis]
---

# Music & Audio Creation

Everything for music creation, AI music generation, and audio analysis.

## 1. Songwriting Craft

### Song Structure
```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse                    (jazz standards)
AAA     Verse/Verse/Verse (strophic)                (folk, storytelling)
```

### Rhyme & Meter
- Mix rhyme types: perfect, family, assonance, consonance, near/slant
- Internal rhyme creates echoes within lines
- Match stressed syllables between parallel lines
- Say it out loud — if you stumble, the meter needs work

### Suno AI Prompt Engineering
**Style field formula:** Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics
```
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky sultry female vocalist, big band jazz, brass section with trumpets and french horns, sweeping strings, minor key, vintage analog warmth"
```

**Metatags (in lyrics field):** `[Verse]` `[Chorus]` `[Whispered]` `[Belted]` `[High Energy]` `[Female Vocals]`

**Phonetic tricks:** Spell words as they sound ("through" → "thru"), ALL CAPS for intensity, vowel extension for sustain ("lo-o-o-ove").

## 2. HeartMuLa — Open-Source Music Generation

Apache-2.0 music foundation model. Generates full songs from lyrics + tags. Comparable to Suno.

**Hardware:** 8GB VRAM min (with `--lazy_load true`), 16GB+ recommended

**Install:**
```bash
git clone https://github.com/HeartMuLa/heartlib.git && cd heartlib
uv venv --python 3.10 .venv && . .venv/bin/activate
uv pip install -e . && uv pip install --upgrade datasets transformers
```

**Generate:**
```bash
python ./examples/run_music_generation.py \
  --model_path=./ckpt --version="3B" \
  --lyrics="./assets/lyrics.txt" --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" --lazy_load true
```

**Tags:** comma-separated, no spaces: `piano,happy,wedding,synthesizer,romantic`

**Lyrics format:**
```
[Intro]
[Verse]
Your lyrics here...
[Chorus]
Chorus lyrics...
```

**Pitfalls:** Don't use bf16 for HeartCodec (degrades quality). Tags may be ignored (known issue #90). RTF ≈ 1.0.

## 3. AudioCraft — Meta's Music/Audio Generation

**MusicGen** (text-to-music), **AudioGen** (text-to-sound), **EnCodec** (neural codec).

**Quick start:**
```python
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained('facebook/musicgen-medium')
model.set_generation_params(duration=30, top_k=250, temperature=1.0, cfg_coef=3.0)
wav = model.generate(["epic orchestral soundtrack with strings"])
torchaudio.save("output.wav", wav[0].cpu(), sample_rate=32000)
```

**Model sizes:** small (300M, ~4GB), medium (1.5B, ~8GB), large (3.3B, ~16GB)

**Melody-conditioned:** `model.generate_with_chroma(descriptions, melody, sr)`

**AudioGen (sound effects):**
```python
from audiocraft.models import AudioGen
model = AudioGen.get_pretrained('facebook/audiogen-medium')
model.set_generation_params(duration=5)
wav = model.generate(["dog barking in a park with birds chirping"])
```

## 4. Audio Analysis — songsee

Generate spectrograms and audio feature visualizations.

**Install:** `go install github.com/steipete/songsee/cmd/songsee@latest`

**Usage:**
```bash
songsee track.mp3                                          # basic spectrogram
songsee track.mp3 --viz spectrogram,mel,chroma,mfcc        # multi-panel grid
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg   # time slice
```

**Visualization types:** spectrogram, mel, chroma, hpss, selfsim, loudness, tempogram, mfcc, flux

**Flags:** `--style classic|magma|inferno|viridis`, `--width/--height`, `--min-freq/--max-freq`

## Choosing the Right Tool

| Need | Tool | Notes |
|------|------|-------|
| Song from lyrics + tags | HeartMuLa | Open-source, local, Apache-2.0 |
| Song with Suno quality | Suno | Cloud service, best quality |
| Text-to-instrumental | AudioCraft MusicGen | Meta, multiple model sizes |
| Sound effects | AudioCraft AudioGen | Environmental sounds |
| Audio visualization | songsee | Spectrograms, MFCC, chroma |
| Songwriting guidance | This skill §1 | Structure, rhyme, meter |
