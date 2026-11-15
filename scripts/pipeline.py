import os
import sys
import shutil
import time
import yaml
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from ffmpeg_utils import get_ffmpeg_paths, get_media_info
from silence_remover import remove_dead_air
from audio_enhancer import enhance_audio
from subtitle_generator import generate_subtitles, burn_subtitles_into_video

def load_config(config_path="config.yaml"):
    """Loads configuration from YAML file."""
    p = Path(config_path)
    if not p.is_file():
        # Look in workspace root
        p = SCRIPT_DIR.parent / "config.yaml"
    if not p.is_file():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def process_video(video_path, config=None, custom_output_name=None):
    """
    Main automated editing pipeline:
      Raw Video 
        -> 1. Silence & Dead-Air Removal (Jump cuts)
        -> 2. Audio Noise Removal & Normalization
        -> 3. Creative Subtitle Generation (Emphasis + Bold)
        -> 4. Burn-in & Export to out/
    """
    start_time = time.time()
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    if config is None:
        config = load_config()

    pipe_cfg = config.get("pipeline", {})
    silence_cfg = config.get("silence_removal", {})
    audio_cfg = config.get("audio_cleaning", {})
    sub_cfg = config.get("subtitles", {})

    workspace_dir = SCRIPT_DIR.parent
    out_dir = workspace_dir / pipe_cfg.get("out_dir", "out")
    temp_dir = workspace_dir / pipe_cfg.get("temp_dir", "temp")
    archive_dir = workspace_dir / pipe_cfg.get("archive_dir", "raw/processed")

    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    base_name = custom_output_name or video_path.stem
    print("\n" + "=" * 65)
    print(f"🎬 PROCESSING VIDEO: {video_path.name}")
    print("=" * 65)

    current_video = video_path

    # --------------------------------------------------------------------------
    # Step 1: Dead-Air & Silence Removal
    # --------------------------------------------------------------------------
    if silence_cfg.get("enabled", True):
        print("\n[Step 1/4] Running Dead-Air Cancellation (Jump-Cuts)...")
        trimmed_video = temp_dir / f"{base_name}_trimmed.mp4"
        current_video = remove_dead_air(
            input_video=current_video,
            output_video=trimmed_video,
            noise_threshold_db=silence_cfg.get("noise_threshold_db", -32),
            min_silence_duration=silence_cfg.get("min_silence_duration", 0.5),
            padding_duration=silence_cfg.get("padding_duration", 0.12),
            temp_dir=temp_dir
        )
    else:
        print("\n[Step 1/4] Dead-Air Removal skipped (disabled in config).")

    # --------------------------------------------------------------------------
    # Step 2: Audio Denoising & Loudness Enhancement
    # --------------------------------------------------------------------------
    if audio_cfg.get("enabled", True):
        print("\n[Step 2/4] Running Audio Cleaning & Noise Removal...")
        denoised_video = temp_dir / f"{base_name}_denoised.mp4"
        current_video = enhance_audio(
            input_video=current_video,
            output_video=denoised_video,
            denoise_amount_db=audio_cfg.get("denoise_amount_db", 12),
            highpass_freq=audio_cfg.get("highpass_frequency", 75),
            normalize=audio_cfg.get("loudness_normalize", True)
        )
    else:
        print("\n[Step 2/4] Audio Cleaning skipped (disabled in config).")

    # --------------------------------------------------------------------------
    # Step 3: Subtitle Generation (Creative Word-Level Emphasis)
    # --------------------------------------------------------------------------
    ass_file = out_dir / f"{base_name}.ass"
    srt_file = out_dir / f"{base_name}.srt"
    subtitles_generated = False

    if sub_cfg.get("enabled", True):
        print("\n[Step 3/4] Transcribing & Generating Creative Bold Subtitles...")
        gen_ass, gen_srt = generate_subtitles(
            video_path=current_video,
            output_ass_path=ass_file,
            output_srt_path=srt_file if sub_cfg.get("save_subtitle_files", True) else None,
            config=config
        )
        subtitles_generated = bool(gen_ass and Path(gen_ass).exists())
    else:
        print("\n[Step 3/4] Subtitles skipped (disabled in config).")

    # --------------------------------------------------------------------------
    # Step 4: Final Assembly & Burn-in
    # --------------------------------------------------------------------------
    final_output = out_dir / f"{base_name}_edited.mp4"
    print("\n[Step 4/4] Finalizing Output Video...")

    if subtitles_generated and sub_cfg.get("burn_into_video", True):
        print(f"[Export] Burning styled subtitles into final video: {final_output.name}")
        burn_subtitles_into_video(
            input_video=current_video,
            ass_subtitle_path=ass_file,
            output_video=final_output
        )
    else:
        print(f"[Export] Copying finalized video to: {final_output.name}")
        shutil.copy2(current_video, final_output)

    # --------------------------------------------------------------------------
    # Step 5: Archive & Cleanup
    # --------------------------------------------------------------------------
    if pipe_cfg.get("archive_processed", True):
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest_archive = archive_dir / video_path.name
        # If destination already exists, rename with timestamp
        if dest_archive.exists():
            dest_archive = archive_dir / f"{video_path.stem}_{int(time.time())}{video_path.suffix}"
        try:
            shutil.move(str(video_path), str(dest_archive))
            print(f"[Archive] Moved raw recording to: {dest_archive.relative_to(workspace_dir)}")
        except Exception as e:
            print(f"[Archive] Notice: could not move raw file: {e}")

    # Remove temp files for this video
    for temp_f in temp_dir.glob(f"{base_name}_*.*"):
        try:
            temp_f.unlink()
        except Exception:
            pass

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"✅ EDITING COMPLETE in {elapsed:.1f} seconds!")
    print(f"📁 Output Video:    {final_output}")
    if subtitles_generated:
        print(f"📄 Subtitles (ASS): {ass_file}")
        print(f"📄 Subtitles (SRT): {srt_file}")
    print("=" * 65 + "\n")

    return final_output

