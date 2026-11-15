import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from ffmpeg_utils import get_ffmpeg_paths, run_command

def enhance_audio(
    input_video, 
    output_video, 
    denoise_amount_db=12, 
    highpass_freq=90, 
    vocal_clarity_boost=True,
    dynamic_leveling=True,
    normalize=True
):
    """
    Applies audio noise reduction, low-frequency rumble filtering,
    vocal clarity presence boosting (for muffled/poor mics),
    dynamic speech leveling, and broadcast loudness normalization (-14 LUFS).
    """
    ffmpeg_exe, _ = get_ffmpeg_paths()
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    print(f"[Audio Enhancement] Cleaning & optimizing audio for: {Path(input_video).name}...")

    audio_filters = []
    
    # 1. High-pass filter to eliminate sub-bass rumble, table thumps, AC hum (< 90 Hz)
    if highpass_freq and highpass_freq > 0:
        audio_filters.append(f"highpass=f={highpass_freq}")

    # 2. Adaptive FFT noise reduction to eliminate continuous hiss and fan noise
    if denoise_amount_db and denoise_amount_db > 0:
        audio_filters.append(f"afftdn=nr={denoise_amount_db}:nf=-30")

    # 3. Vocal Clarity Boost (De-muffles poor mics & cuts boxy room echo)
    if vocal_clarity_boost:
        # A. De-box EQ: cuts 350 Hz by 3.5 dB to remove hollow room reflection / boxy laptop mic tone
        audio_filters.append("equalizer=f=350:width_type=h:width=160:g=-3.5")
        # B. Vocal Presence & Consonant EQ: boosts 3.2 kHz by +4.5 dB (brings out 's', 't', 'p', 'k' clarity)
        audio_filters.append("equalizer=f=3200:width_type=h:width=1400:g=4.5")
        print("[Audio Enhancement] Vocal Clarity Boost enabled (De-box EQ + 3.2kHz Presence Boost).")

    # 4. Dynamic Speech Leveler (boosts quiet/mumbled words and levels inconsistent volume)
    if dynamic_leveling:
        audio_filters.append("speechnorm=e=4:r=0.0001:l=1")
        print("[Audio Enhancement] Dynamic Speech Leveling enabled (speechnorm).")

    # 5. EBU R128 Loudness Normalization for YouTube broadcast standard (-14 LUFS)
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

    print(f"[Audio Enhancement] Applying filter chain...")
    run_command(cmd)
    print("[Audio Enhancement] Audio successfully enhanced (vocals de-muffled, leveled & noise removed).")
    return output_video
