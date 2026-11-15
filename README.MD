# YT Pipeline

A local, automated Python and FFmpeg pipeline that handles the mechanical, repetitive parts of video editing for YouTube: removing dead air, enhancing audio clarity & speech leveling, generating creative bold captions with native Hinglish support (no unwanted English translation), and exporting either standard 16:9 Long-Form or 9:16 Shorts. You record, it produces a polished rough cut, and you finish it manually.

It does **not** write your content, generate synthetic AI videos, or upload anything. Everything runs locally and is 100% free.

---

## ⚡ What it does

Given one recording in `raw/`, it produces in `out/`:

| Output | Description |
|---|---|
| `<name>_edit.mp4` | 1080p horizontal video with silences removed, audio cleaned/normalized, and subtitles burned in |
| `<name>.srt` | Standard captions file (for uploading to YouTube Studio) |
| `<name>.ass` | Advanced SubStation Alpha stylized captions with bold emphasis |
| `<name>_transcript.txt` | Plain-text transcript (useful for writing titles, descriptions, and chapters) |
| `<name>_short.mp4` | 9:16 center-cropped vertical version with captions burned in for YouTube Shorts |

---

## 📂 Project Structure

```
yt-pipeline/
├── .gitignore                # Ignores heavy video binaries, temp files, and caches
├── config.yaml               # Pipeline settings (silence sensitivity, audio, subtitles)
├── README.md                 # Project documentation and guide
├── requirements.txt          # Python dependencies (faster-whisper, SpeechRecognition, pyyaml, watchdog)
├── start_watcher.bat         # 1-click launcher to run background folder watcher
├── raw/                      # 📥 Place your raw recordings here (.mp4, .mov, .mkv)
│   ├── .gitkeep
│   └── processed/            # 📦 Finished recordings are archived here
│       └── .gitkeep
├── out/                      # 📤 Generated edited videos, shorts, and transcripts
│   └── .gitkeep
└── scripts/
    ├── process.py            # Main entry point (CLI & positional arguments)
    ├── watcher.py            # Continuous folder watcher
    ├── pipeline.py           # Core multi-step editing coordinator
    ├── silence_remover.py    # Dead-air silence detection & cutting
    ├── audio_enhancer.py     # FFT noise reduction, vocal clarity EQ & YouTube loudness normalization
    ├── subtitle_generator.py # Word-level transcription, bold styling & resolution auto-scaling
    ├── hinglish_utils.py     # Devanagari to conversational Latin Hinglish transliterator
    └── ffmpeg_utils.py       # FFmpeg integration & hardware checks
```

---

## 🛠️ Requirements & Installation

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: 3.10 or newer
- **FFmpeg**: Required for audio/video processing and subtitle rendering

### 1. Install FFmpeg
- **Windows (Winget)**:
  ```powershell
  winget install Gyan.FFmpeg
  ```
  *(Restart your terminal after installation, then verify with `ffmpeg -version`)*
- **macOS (Homebrew)**:
  ```bash
  brew install ffmpeg
  ```
- **Linux (Debian/Ubuntu)**:
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```
*(The first run downloads the local Whisper model ~140MB, which needs an internet connection once.)*

### 3. Verify Setup
Run the built-in self-test to verify FFmpeg, audio filters, and subtitle engines:
```bash
python scripts/process.py --test
```

---

## 🚀 Usage

### Option 1: Automated Background Watcher (Recommended)
Double-click `start_watcher.bat` or run:
```bash
python scripts/process.py --watch
```
Now, simply save your OBS recordings or drop video files into `raw/`. The pipeline automatically detects when writing is complete, edits the video, and saves the output to `out/`.

### Option 2: Edit a Single File
```bash
python scripts/process.py raw/video1.mp4
```
*When running, the script asks you to choose:*
- `[1] Long-Form` -> Normal 16:9 YouTube widescreen (original ratio as-is).
- `[2] Short-Form` -> 9:16 vertical crop for YouTube Shorts / Reels.

You can also skip the prompt using direct CLI flags:
```bash
python scripts/process.py raw/video1.mp4 --long      # Force standard 16:9 normal ratio
python scripts/process.py raw/video1.mp4 --short     # Force 9:16 vertical crop
python scripts/process.py raw/video1.mp4 --no-silence # Skip silence removal
python scripts/process.py raw/video1.mp4 --no-denoise # Skip audio cleaning
```

### Option 3: Process All Videos in `raw/`
```bash
python scripts/process.py --all
```

---

## ⚙️ Configuration (`config.yaml`)

```yaml
# Silence & Dead-Air Removal
silence_removal:
  enabled: true
  noise_threshold_db: -32          # Audio below this dB level is considered silence
  min_silence_duration: 0.5        # Minimum silent pause (in seconds) to cut out
  padding_duration: 0.12           # Safe margin (seconds) kept around speech

# Audio Cleaning & Vocal Clarity Enhancement
audio_cleaning:
  enabled: true
  denoise_amount_db: 12            # FFT denoiser strength in dB
  highpass_frequency: 90           # Cuts low rumble below 90 Hz
  vocal_clarity_boost: true        # De-muffles poor mics (cuts 350Hz hollow echo & boosts 3.2kHz presence)
  dynamic_leveling: true           # Levels out quiet/mumbled speech so every syllable is audible
  loudness_normalize: true         # Broadcast speech standard (-14 LUFS)

# Dynamic Subtitles (Native Hinglish & English)
subtitles:
  enabled: true
  model_size: "base"               # tiny, base, small, medium (use "small" for heavy accents)
  language: "hinglish"             # "hinglish" (Hindi spoken words written in Latin script, NO English translation), "en", or "hi"
  hinglish: true                   # Transcribes Hindi speech into natural conversational Latin Hinglish (Gaadi, ghar, sab kuch...)
  max_words_per_segment: 4         # Punchy pacing (3-5 words per line)
  burn_into_video: true            # Burn subtitles into final export
  style:
    font_name: "Arial Black"
    font_size: 48                  # Auto-scaled to video resolution (7.5% of height for 16:9, ~5.8% for Shorts)
    short_font_size: 64            # Scaled for 9:16 Shorts
    primary_color: "&H00FFFFFF"    # White
  emphasis:
    enabled: true
    highlight_color: "&H002BF7F7"  # Vibrant Gold / Yellow (&HAABBGGRR)
    highlight_bold: true           # Adds bold formatting to key words (English & Hinglish)

# Format & Layout Selection
format:
  preference: "ask"                # "ask" (prompts you every time), "long" (16:9 normal), or "short" (9:16 vertical)
  resolution: 1080
```

---

## 💡 Recommended Workflow

1. Plan the video with bullet points rather than a word-for-word script.
2. Record in a reasonably quiet room. If you make a mistake, pause for 2 seconds and re-say the sentence.
3. Save or drop the video into `raw/`.
4. The pipeline automatically removes dead pauses, cleans audio, creates captions with bold keywords, and exports the rough cut.
5. Review `<name>_edit.mp4` in DaVinci Resolve, Premiere Pro, or CapCut if you want to add B-roll, music, or trim specific takes.
6. Use `<name>_transcript.txt` to draft title, video description, and timestamp chapters.

---

## ⚠️ Known Limitations

- **Content judgment**: Silence removal cuts quiet pauses; it cannot tell a bad take from a good take. Always review your rough cut.
- **Whisper names/jargon**: Whisper occasionally mishears proper nouns or niche technical jargon. Skim the generated `.srt` before uploading captions.
- **Center-cropping**: Automatic 9:16 center-cropping works great for talking heads and webcam footage, but might cut off edges on full-desktop screen recordings. Check `<name>_short.mp4` before posting.
- **CPU vs GPU**: CPU transcription with `base` takes only seconds. If you switch to `medium` or `large` models, consider using an NVIDIA GPU (CUDA).
