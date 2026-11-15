import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def get_ffmpeg_paths():
    """
    Locates ffmpeg and ffprobe, refreshing PATH from registry or checking
    WinGet links directory if not found in current process environment.
    """
    ffmpeg_exe = shutil.which("ffmpeg")
    ffprobe_exe = shutil.which("ffprobe")

    if not ffmpeg_exe or not ffprobe_exe:
        # Check WinGet link directory directly
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        winget_links = os.path.join(local_app_data, "Microsoft", "WinGet", "Links")
        if os.path.exists(winget_links):
            os.environ["PATH"] = winget_links + os.pathsep + os.environ.get("PATH", "")
            ffmpeg_exe = shutil.which("ffmpeg")
            ffprobe_exe = shutil.which("ffprobe")

    if not ffmpeg_exe or not ffprobe_exe:
        # Try refreshing environment PATH from Windows registry
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                system_path, _ = winreg.QueryValueEx(key, "Path")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                user_path, _ = winreg.QueryValueEx(key, "Path")
            full_path = system_path + os.pathsep + user_path
            os.environ["PATH"] = full_path + os.pathsep + os.environ.get("PATH", "")
            ffmpeg_exe = shutil.which("ffmpeg")
            ffprobe_exe = shutil.which("ffprobe")
        except Exception:
            pass

    if not ffmpeg_exe or not ffprobe_exe:
        raise FileNotFoundError(
            "FFmpeg or FFprobe could not be located on this system. "
            "Please ensure Gyan.FFmpeg is installed and added to PATH."
        )

    return ffmpeg_exe, ffprobe_exe

FFMPEG_PATH, FFPROBE_PATH = get_ffmpeg_paths()

def run_command(cmd, check=True, capture_output=True, verbose=False):
    """Executes a command and returns subprocess.CompletedProcess."""
    if verbose:
        print(f"[CMD] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if check and result.returncode != 0:
        err_msg = result.stderr if capture_output else f"Command failed with code {result.returncode}"
        raise RuntimeError(f"Command failed:\n{' '.join(str(c) for c in cmd)}\n\nError:\n{err_msg}")
    return result

def get_media_info(file_path):
    """Returns media metadata (duration, width, height, fps, audio channels, etc.)."""
    _, ffprobe = get_ffmpeg_paths()
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    res = run_command(cmd)
    data = json.loads(res.stdout)
    
    info = {
        "duration": float(data.get("format", {}).get("duration", 0)),
        "size_bytes": int(data.get("format", {}).get("size", 0)),
        "has_video": False,
        "has_audio": False,
        "width": 1920,
        "height": 1080,
        "fps": 30.0
    }

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not info["has_video"]:
            info["has_video"] = True
            info["width"] = int(stream.get("width", 1920))
            info["height"] = int(stream.get("height", 1080))
            fps_str = stream.get("avg_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                info["fps"] = float(num) / float(den) if float(den) != 0 else 30.0
            else:
                info["fps"] = float(fps_str)
        elif codec_type == "audio" and not info["has_audio"]:
            info["has_audio"] = True
            info["audio_sample_rate"] = int(stream.get("sample_rate", 44100))

    return info

