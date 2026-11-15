import os
import sys
import time
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from pipeline import load_config, process_video

def is_file_ready(file_path, settle_time=4):
    """
    Checks if a video file has finished copying/writing:
    1. Size must remain constant for at least settle_time seconds.
    2. Must be able to open file for reading without sharing violation.
    """
    try:
        p = Path(file_path)
        if not p.exists() or p.stat().st_size == 0:
            return False

        initial_size = p.stat().st_size
        time.sleep(settle_time)
        
        if not p.exists():
            return False

        if p.stat().st_size != initial_size:
            return False

        # Test exclusive read to confirm write handle is released
        with open(p, "rb") as f:
            f.read(1024)
        return True
    except (PermissionError, OSError):
        return False

def scan_and_process(config):
    """Scans the raw directory and processes any ready video files."""
    pipe_cfg = config.get("pipeline", {})
    watch_cfg = config.get("watcher", {})

    workspace_dir = SCRIPT_DIR.parent
    raw_dir = workspace_dir / pipe_cfg.get("raw_dir", "raw")
    archive_dir = workspace_dir / pipe_cfg.get("archive_dir", "raw/processed")
    supported_exts = tuple(watch_cfg.get("supported_extensions", [".mp4", ".mov", ".mkv", ".webm", ".avi"]))
    settle_time = watch_cfg.get("settle_time_sec", 4)

    raw_dir.mkdir(parents=True, exist_ok=True)

    # Find files in raw/ (excluding subdirectories like processed/)
    video_files = [
        f for f in raw_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_exts and not f.name.startswith(".")
    ]

    for video_file in video_files:
        print(f"\n[Watcher] Found incoming recording: {video_file.name}")
        print(f"[Watcher] Verifying file write completion (settle time {settle_time}s)...")

        if is_file_ready(video_file, settle_time=settle_time):
            print(f"[Watcher] File is ready! Starting automated editing...")
            try:
                process_video(video_file, config=config)
            except Exception as e:
                print(f"[Watcher] ERROR processing {video_file.name}: {e}")
        else:
            print(f"[Watcher] File {video_file.name} is still being written or copied. Waiting...")

def run_watcher():
    """Starts the continuous folder monitoring loop."""
    config = load_config()
    pipe_cfg = config.get("pipeline", {})
    watch_cfg = config.get("watcher", {})
    poll_interval = watch_cfg.get("poll_interval_sec", 2)
    raw_dir = SCRIPT_DIR.parent / pipe_cfg.get("raw_dir", "raw")

    print("\n" + "=" * 65)
    print("👀 YOUTUBE VIDEO AUTOMATION WATCHER ACTIVE")
    print(f"📂 Watching Folder:   {raw_dir.resolve()}")
    print(f"⚙️  Poll Interval:     {poll_interval}s")
    print("👉 Simply save or drop your raw video recordings into 'raw/'")
    print("   The pipeline will automatically edit and export them to 'out/'")
    print("   Press Ctrl + C at any time to stop.")
    print("=" * 65 + "\n")

    try:
        while True:
            scan_and_process(config)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n[Watcher] Stopped by user.")

if __name__ == "__main__":
    run_watcher()

