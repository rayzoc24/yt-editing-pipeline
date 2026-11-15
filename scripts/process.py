import os
import sys
import argparse
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from pipeline import load_config, process_video
from watcher import run_watcher, scan_and_process

def process_single(file_path, config, **kwargs):
    """Processes a single video file."""
    p = Path(file_path).resolve()
    if not p.is_file():
        print(f"Error: Video file not found: {p}")
        sys.exit(1)
    process_video(p, config=config, **kwargs)

def process_all_existing(config, **kwargs):
    """Processes all video files currently in raw/."""
    pipe_cfg = config.get("pipeline", {})
    watch_cfg = config.get("watcher", {})
    workspace_dir = SCRIPT_DIR.parent
    raw_dir = workspace_dir / pipe_cfg.get("raw_dir", "raw")
    supported_exts = tuple(watch_cfg.get("supported_extensions", [".mp4", ".mov", ".mkv", ".webm", ".avi"]))

    files = [
        f for f in raw_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_exts and not f.name.startswith(".")
    ]

    if not files:
        print(f"[Process] No unprocessed video files found in {raw_dir}")
        return

    print(f"[Process] Found {len(files)} video(s) in {raw_dir}:")
    for f in files:
        print(f" - {f.name}")

    for f in files:
        process_video(f, config=config, **kwargs)

def run_self_test(config):
    """
    Creates a 6-second synthetic test video with silence gaps and speech tone,
    then runs it through the entire editing pipeline to test dead-air removal,
    audio filtering, and subtitle styling.
    """
    from ffmpeg_utils import get_ffmpeg_paths, run_command

    print("\n🧪 RUNNING PIPELINE SELF-TEST...")
    ffmpeg_exe, _ = get_ffmpeg_paths()
    temp_dir = SCRIPT_DIR.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    test_video = temp_dir / "pipeline_test_raw.mp4"

    # Create a 6s video with 2s tone, 2s silence, 2s tone
    print("[Test] Generating synthetic test video with dead-air gap...")
    test_filter = (
        "sine=frequency=440:duration=2 [s1]; "
        "aevalsrc=0:duration=2 [s2]; "
        "sine=frequency=520:duration=2 [s3]; "
        "[s1][s2][s3]concat=n=3:v=0:a=1[aout]; "
        "color=c=navy:s=1280x720:d=6[vout]"
    )
    cmd = [
        ffmpeg_exe,
        "-y",
        "-filter_complex", test_filter,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-t", "6",
        str(test_video)
    ]
    run_command(cmd)
    print(f"[Test] Test video generated: {test_video}")

    # Process without archive
    cfg_copy = dict(config)
    cfg_copy["pipeline"] = dict(cfg_copy.get("pipeline", {}))
    cfg_copy["pipeline"]["archive_processed"] = False
    
    # Run test through pipeline
    out_file = process_video(test_video, config=cfg_copy, custom_output_name="pipeline_selftest")
    print(f"\n🎉 SELF-TEST SUCCEEDED! Verified output at: {out_file}\n")

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Automated Raw Video Editing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/process.py raw/video1.mp4   # Edit a specific video
  python scripts/process.py --watch          # Run continuous folder watcher
  python scripts/process.py --all            # Process all videos currently in raw/
  python scripts/process.py --test           # Run system self-test
        """
    )
    parser.add_argument("video", nargs="?", type=str, help="Path to raw video file to process")
    parser.add_argument("--watch", "-w", action="store_true", help="Start continuous folder watcher")
    parser.add_argument("--file", "-f", type=str, help="Process a single video file")
    parser.add_argument("--all", "-a", action="store_true", help="Process all videos in raw/")
    parser.add_argument("--test", "-t", action="store_true", help="Run a self-test with a synthetic video")
    parser.add_argument("--no-short", action="store_true", help="Skip 9:16 Shorts export")
    parser.add_argument("--no-silence", action="store_true", help="Disable dead-air removal")
    parser.add_argument("--no-denoise", action="store_true", help="Disable audio noise reduction")
    parser.add_argument("--no-subtitles", action="store_true", help="Disable subtitles")
    parser.add_argument("--config", "-c", type=str, default="config.yaml", help="Path to config.yaml")

    args = parser.parse_args()
    config = load_config(args.config)

    # Apply CLI overrides to config
    if args.no_silence:
        config["silence_removal"]["enabled"] = False
    if args.no_denoise:
        config["audio_cleaning"]["enabled"] = False
    if args.no_subtitles:
        config["subtitles"]["enabled"] = False

    target_file = args.video or args.file

    if args.test:
        run_self_test(config)
    elif target_file:
        process_single(target_file, config, no_short=args.no_short)
    elif args.all:
        process_all_existing(config, no_short=args.no_short)
    elif args.watch:
        run_watcher()
    else:
        # Default behavior: run continuous watcher
        run_watcher()

if __name__ == "__main__":
    main()

