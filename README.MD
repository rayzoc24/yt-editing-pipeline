# 🎬 Automated YouTube Raw Video Editing Pipeline

An automated 90% raw editing pipeline built with Python and FFmpeg. As soon as you record or drop a video into `raw/`, this pipeline automatically processes and exports a polished cut to `out/`.

---

## ⚡ What It Does Automatically

1. **Dead-Air & Silence Removal (Jump Cuts)**
   - Analyzes audio volume and detects silent pauses (default: sounds below `-32 dB` lasting longer than `0.5s`).
   - Cuts out dead air while preserving natural speech padding (`0.12s`) so words never get clipped.
   - Smoothly jump-cuts video segments together.

2. **Noise Removal & Vocal Enhancement**
   - Applies adaptive FFT noise reduction (`afftdn`) to remove computer fans, AC noise, and background hiss.
   - High-pass filter (`75 Hz`) removes table bumps, mic rumbles, and electrical hums.
   - Standardizes broadcast speech volume to YouTube's target (-14 LUFS) with dynamic loudness normalization.

3. **Creative Bold Subtitles**
   - Uses local `faster-whisper` for word-level speech-to-text.
   - Breaks text into punchy 3-5 word subtitle lines.
   - **Smart Emphasis Highlighting**: Automatically detects key keywords, numbers, and impact words, applying **Bold** (`{\b1}`) and vibrant gold/yellow highlighting (`#F7F72B`) over crisp white text with a black outline and soft shadow.
   - Burns subtitles directly into the video and also exports `.ass` and `.srt` files.

4. **Continuous Drop-Folder Automation (Watcher)**
   - Monitors `raw/` in the background.
   - Waits for OBS / screen recordings or camera transfers to finish copying before starting.
   - Archives raw source files to `raw/processed/` when finished.

---

## 📂 Project Structure

```
youtube/
├── .gitignore                # Prevents large video files & cache from being tracked
├── config.yaml               # Pipeline settings (silence sensitivity, fonts, colors)
├── README.MD                 # Project documentation & usage guide
├── requirements.txt          # Python dependencies (faster-whisper, pyyaml, watchdog)
├── start_watcher.bat         # 1-click launcher to run the automated folder watcher
├── raw/                      # 📥 DROP YOUR RAW RECORDINGS HERE (.mp4, .mov, .mkv)
│   ├── .gitkeep
│   └── processed/            # 📦 Completed raw recordings are safely moved here
│       └── .gitkeep
├── out/                      # 📤 EDITED VIDEOS & SUBTITLES APPEAR HERE
│   └── .gitkeep
└── scripts/
    ├── process.py            # Primary CLI tool
    ├── watcher.py            # Automatic folder watcher
    ├── pipeline.py           # Core multi-step editing coordinator
    ├── silence_remover.py    # Dead-air silence detection & cutting
    ├── audio_enhancer.py     # Noise reduction & loudness normalization
    ├── subtitle_generator.py # Word-level transcription, styling & burn-in
    └── ffmpeg_utils.py       # FFmpeg integration & hardware checks
```

---

## 🛠️ Prerequisites & Installation

### 1. Install FFmpeg
- **Windows (Winget)**:
  ```powershell
  winget install Gyan.FFmpeg
  ```
- **macOS (Homebrew)**:
  ```bash
  brew install ffmpeg
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

### 2. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🚀 How to Use

### Mode 1: Automated Background Watcher (Recommended)
Double-click `start_watcher.bat` (or run in terminal):
```powershell
python scripts/process.py --watch
```
Now, simply save or copy any video file into `raw/`. The pipeline will automatically detect it, edit it, and place the finished video in `out/`.

### Mode 2: Edit a Single File
```powershell
python scripts/process.py --file raw/my_video.mp4
```

### Mode 3: Edit All Videos in `raw/`
```powershell
python scripts/process.py --all
```

### Mode 4: Self-Test Verification
```powershell
python scripts/process.py --test
```

---

## ⚙️ Customization (`config.yaml`)

You can adjust any settings in [config.yaml](file:///c:/Users/Shreeyash%20kulkarni/OneDrive/Desktop/youtube/config.yaml):
- **Silence cut sensitivity**: change `noise_threshold_db` (e.g. `-30` for aggressive cuts, `-35` for subtle cuts) and `min_silence_duration` (e.g. `0.4` seconds).
- **Noise reduction level**: change `denoise_amount_db` (default `12 dB`).
- **Subtitle font**: change `font_name` (e.g., `Arial Black`, `Montserrat`, `Impact`).
- **Highlight color**: change `highlight_color` (ASS hex format: `&HAABBGGRR`).
- **Burn-in**: set `burn_into_video: false` if you only want standalone `.ass`/`.srt` files for Premiere / DaVinci Resolve.
