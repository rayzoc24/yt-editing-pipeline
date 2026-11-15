# YT Pipeline

A local, automated Python and FFmpeg pipeline that handles the mechanical, repetitive parts of video editing for YouTube: removing dead air, normalizing audio, generating creative bold captions, and exporting a 9:16 Shorts cut. You record, it produces a polished rough cut, and you finish it manually.

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
├── requirements.txt          # Python dependencies (faster-whisper, pyyaml, watchdog)
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
    ├── audio_enhancer.py     # FFT noise reduction & YouTube loudness normalization
    ├── subtitle_generator.py # Word-level transcription, bold styling & 9:16 crop
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

Optional CLI flags:
```bash
python scripts/process.py raw/video1.mp4 --no-short     # Skip the 9:16 Shorts export
python scripts/process.py raw/video1.mp4 --no-silence   # Skip silence removal
python scripts/process.py raw/video1.mp4 --no-denoise   # Skip audio cleaning
python scripts/process.py raw/video1.mp4 --config my.yaml
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

# Audio Cleaning & Normalization
audio_cleaning:
  enabled: true
  denoise_amount_db: 12            # FFT denoiser strength in dB
  highpass_frequency: 75           # Cuts low rumble below 75 Hz
  loudness_normalize: true         # Broadcast speech standard (-14 LUFS)

# Dynamic Subtitles
subtitles:
  enabled: true
  model_size: "base"               # tiny, base, small, medium
  language: "en"                   # "en", "hi", etc. or null for auto-detect
  max_words_per_segment: 4         # Punchy pacing (3-5 words per line)
  burn_into_video: true            # Burn subtitles into final export
  style:
    font_name: "Arial Black"
    font_size: 20
    primary_color: "&H00FFFFFF"    # White
  emphasis:
    enabled: true
    highlight_color: "&H002BF7F7"  # Vibrant Gold / Yellow
    highlight_bold: true           # Adds bold formatting to key words

# Export Options
export:
  shorts: true                     # Generate 9:16 vertical center-crop
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
