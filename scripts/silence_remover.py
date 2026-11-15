import os
import re
import subprocess
from pathlib import Path
from ffmpeg_utils import get_ffmpeg_paths, get_media_info, run_command

def detect_silence_intervals(video_path, noise_threshold_db=-32, min_silence_duration=0.5):
    """
    Uses ffmpeg silencedetect filter to find silence intervals in the video.
    Returns a list of tuples: [(silence_start, silence_end), ...]
    """
    ffmpeg_exe, _ = get_ffmpeg_paths()
    cmd = [
        ffmpeg_exe,
        "-hide_banner",
        "-i", str(video_path),
        "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_silence_duration}",
        "-f", "null",
        "-"
    ]

    res = run_command(cmd, check=False, capture_output=True)
    stderr = res.stderr

    silence_starts = []
    silence_ends = []
    
    start_pattern = re.compile(r"silence_start:\s*([0-9.]+)")
    end_pattern = re.compile(r"silence_end:\s*([0-9.]+)")

    for line in stderr.splitlines():
        start_match = start_pattern.search(line)
        if start_match:
            silence_starts.append(float(start_match.group(1)))
        end_match = end_pattern.search(line)
        if end_match:
            silence_ends.append(float(end_match.group(1)))

    # Match starts and ends
    intervals = []
    total_duration = get_media_info(video_path)["duration"]

    for i in range(len(silence_starts)):
        start = silence_starts[i]
        end = silence_ends[i] if i < len(silence_ends) else total_duration
        if end > start:
            intervals.append((start, end))

    return intervals, total_duration

def calculate_speech_segments(silence_intervals, total_duration, padding=0.12):
    """
    Inverts silence intervals to speech intervals, adding padding around speech
    and merging any overlapping segments.
    """
    if not silence_intervals:
        return [(0.0, total_duration)]

    speech_segments = []
    current_time = 0.0

    for s_start, s_end in silence_intervals:
        seg_start = current_time
        seg_end = s_start + padding
        
        # Don't cut into preceding speech
        if seg_end > seg_start:
            speech_segments.append((seg_start, min(total_duration, seg_end)))
        
        current_time = max(0.0, s_end - padding)

    if current_time < total_duration:
        speech_segments.append((current_time, total_duration))

    # Merge overlapping or touching segments
    merged = []
    for start, end in speech_segments:
        if end <= start:
            continue
        if not merged:
            merged.append([start, end])
        else:
            prev = merged[-1]
            if start <= prev[1] + 0.05:  # within 50ms, merge
                prev[1] = max(prev[1], end)
            else:
                merged.append([start, end])

    return [(m[0], m[1]) for m in merged]

def remove_dead_air(input_video, output_video, noise_threshold_db=-32, min_silence_duration=0.5, padding_duration=0.12, temp_dir="temp", **kwargs):
    """
    Cuts dead air from input_video and saves the trimmed video to output_video.
    """
    padding = kwargs.get("padding", padding_duration)
    ffmpeg_exe, _ = get_ffmpeg_paths()
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    print(f"[Dead-Air Removal] Analyzing silence in: {Path(input_video).name}...")
    silence_intervals, total_duration = detect_silence_intervals(
        input_video,
        noise_threshold_db=noise_threshold_db,
        min_silence_duration=min_silence_duration
    )

    if not silence_intervals:
        print("[Dead-Air Removal] No significant silence detected. Copying source stream.")
        run_command([ffmpeg_exe, "-y", "-i", str(input_video), "-c", "copy", str(output_video)])
        return output_video

    speech_segments = calculate_speech_segments(silence_intervals, total_duration, padding=padding)
    kept_duration = sum(end - start for start, end in speech_segments)
    cut_seconds = total_duration - kept_duration
    print(f"[Dead-Air Removal] Detected {len(silence_intervals)} silent pauses.")
    print(f"[Dead-Air Removal] Original duration: {total_duration:.1f}s -> Trimmed duration: {kept_duration:.1f}s (Cut {cut_seconds:.1f}s of dead air)")

    if len(speech_segments) == 1 and speech_segments[0][0] == 0.0 and speech_segments[0][1] >= total_duration:
        run_command([ffmpeg_exe, "-y", "-i", str(input_video), "-c", "copy", str(output_video)])
        return output_video

    # Build filter_complex for seamless concat
    filter_parts = []
    concat_inputs = []

    for idx, (start, end) in enumerate(speech_segments):
        filter_parts.append(f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{idx}]")
        filter_parts.append(f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        concat_inputs.append(f"[v{idx}][a{idx}]")

    num_segments = len(speech_segments)
    concat_filter = f"{''.join(concat_inputs)}concat=n={num_segments}:v=1:a=1[outv][outa]"
    filter_complex_str = ";".join(filter_parts) + ";" + concat_filter

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_video),
        "-filter_complex", filter_complex_str,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_video)
    ]

    print("[Dead-Air Removal] Rendering jump-cut video...")
    run_command(cmd)

    return output_video
