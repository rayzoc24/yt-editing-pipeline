import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from ffmpeg_utils import get_ffmpeg_paths, run_command

def enhance_audio(input_video, output_video, denoise_amount_db=12, highpass_freq=75, normalize=True):
    """
    Applies audio noise reduction, low-frequency rumble filtering, and
    broadcast loudness normalization (-14 LUFS for YouTube).
    Video stream is copied without re-encoding to save time and maintain full visual fidelity.
    """
    ffmpeg_exe, _ = get_ffmpeg_paths()
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    print(f"[Audio Enhancement] Cleaning audio in: {Path(input_video).name}...")

    # Build audio filter chain
    audio_filters = []
    
    # 1. High-pass filter to cut out table thumps, AC hum, sub-bass rumble
    if highpass_freq and highpass_freq > 0:
        audio_filters.append(f"highpass=f={highpass_freq}")

    # 2. Adaptive FFT noise reduction
    if denoise_amount_db and denoise_amount_db > 0:
        # afftdn: nr = noise reduction (dB), nf = noise floor (dB)
        audio_filters.append(f"afftdn=nr={denoise_amount_db}:nf=-30")

    # 3. EBU R128 loudness normalization for YouTube speech standard
    if normalize:
        audio_filters.append("loudnorm=I=-14:TP=-1.5:LRA=7")

    filter_str = ",".join(audio_filters)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_video),
        "-c:v", "copy",            # Fast lossless video stream copy
        "-af", filter_str,
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_video)
    ]

    print(f"[Audio Enhancement] Applying filters: {filter_str}")
    run_command(cmd)
    print("[Audio Enhancement] Audio noise removed and vocal levels normalized.")
    return output_video

