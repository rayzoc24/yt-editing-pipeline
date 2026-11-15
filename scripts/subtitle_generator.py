import os
import sys
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from ffmpeg_utils import get_ffmpeg_paths, get_media_info, run_command

# Common filler/stop words that should NOT be emphasized
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", 
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself"
}

# High-impact emotion/emphasis keywords
HIGH_IMPACT_KEYWORDS = {
    "secret", "insane", "crazy", "huge", "massive", "never", "always", "best", "worst", 
    "free", "money", "profit", "mistake", "warning", "danger", "fast", "speed", "easy", 
    "impossible", "ultimate", "hack", "boost", "zero", "first", "million", "billion",
    "stop", "shocking", "critical", "genius", "magic", "win", "fail", "broken", "viral",
    "perfect", "guaranteed", "proven", "hidden", "truth", "exposed", "top", "unbelievable"
}

def format_ass_time(seconds):
    """Converts seconds into ASS timestamp format: H:MM:SS.cc"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def format_srt_time(seconds):
    """Converts seconds into SRT timestamp format: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def is_emphasis_word(word_clean, is_longest=False):
    """Determines if a word should receive creative visual emphasis (bold + color)."""
    if len(word_clean) <= 2:
        return False
    lower = word_clean.lower()
    if lower in STOP_WORDS:
        return False
    
    # 1. Numbers or currency (e.g. 100, $500, 10x, 90%)
    if any(char.isdigit() for char in word_clean) or any(s in word_clean for s in ["$", "%", "k", "x"]):
        return True

    # 2. High-impact keyword matches
    if lower in HIGH_IMPACT_KEYWORDS:
        return True

    # 3. All-caps word (e.g. WOW, DONT, AI)
    if word_clean.isupper() and len(word_clean) >= 2:
        return True

    # 4. Longest key word in the short phrase
    if is_longest and len(word_clean) >= 6:
        return True

    return False

def transcribe_audio_words(audio_or_video_path, model_size="base", language="en"):
    """
    Transcribes audio with faster-whisper and extracts word-level timestamps.
    """
    from faster_whisper import WhisperModel

    print(f"[Subtitles] Loading Whisper model ('{model_size}')...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"[Subtitles] Transcribing audio with word-level timestamps...")
    segments, info = model.transcribe(
        str(audio_or_video_path),
        language=language,
        word_timestamps=True,
        beam_size=5,
        vad_filter=True
    )

    all_words = []
    for segment in segments:
        if segment.words:
            for word_obj in segment.words:
                all_words.append({
                    "word": word_obj.word.strip(),
                    "start": word_obj.start,
                    "end": word_obj.end,
                    "probability": word_obj.probability
                })
    return all_words

def group_words_into_lines(words, max_words=4, max_pause=0.35, max_duration=2.2):
    """
    Chunks words into modern, punchy YouTube subtitle lines (3-5 words max).
    """
    lines = []
    current_chunk = []

    for i, w in enumerate(words):
        if not current_chunk:
            current_chunk.append(w)
            continue

        prev_w = current_chunk[-1]
        pause = w["start"] - prev_w["end"]
        duration = w["end"] - current_chunk[0]["start"]

        # Sentence end punctuation
        prev_has_punct = any(prev_w["word"].endswith(p) for p in [".", "!", "?", "—"])

        if (len(current_chunk) >= max_words or 
            pause > max_pause or 
            duration > max_duration or 
            prev_has_punct):
            lines.append(current_chunk)
            current_chunk = [w]
        else:
            current_chunk.append(w)

    if current_chunk:
        lines.append(current_chunk)

    return lines

def generate_subtitles(video_path, output_ass_path, output_srt_path=None, output_txt_path=None, config=None, is_short=False):
    """
    Transcribes video and writes stylized ASS, SRT subtitles, and plain-text transcript.
    Adapts font size and positioning for standard 16:9 or vertical 9:16 Shorts.
    """
    if config is None:
        config = {}

    sub_cfg = config.get("subtitles", {})
    style_cfg = sub_cfg.get("style", {})
    emph_cfg = sub_cfg.get("emphasis", {})

    model_size = sub_cfg.get("model_size", "base")
    language = sub_cfg.get("language", "en")
    max_words = sub_cfg.get("max_words_per_segment", 4)

    font_name = style_cfg.get("font_name", "Arial Black")
    primary_color = style_cfg.get("primary_color", "&H00FFFFFF")   # White
    outline_color = style_cfg.get("outline_color", "&H00000000")   # Black
    outline_width = style_cfg.get("outline_width", 3.0)
    shadow_depth = style_cfg.get("shadow_depth", 1.5)

    # Probe actual video dimensions to scale subtitles dynamically
    try:
        v_info = get_media_info(video_path)
        v_width = v_info.get("width", 1920)
        v_height = v_info.get("height", 1080)
    except Exception:
        v_width, v_height = 1920, 1080

    if is_short:
        # Vertical 9:16 layout
        res_y = v_height
        res_x = int(v_height * 9 / 16) if v_width > v_height else v_width
        # Subtitle font ~6% of vertical screen height (large, bold mobile text)
        font_size = int(res_y * 0.058)
        alignment = style_cfg.get("short_alignment", 2)  # Bottom-center elevated
        margin_v = int(res_y * 0.22)                     # Safe from bottom title overlay
        outline_width = max(3.5, round(font_size * 0.10, 1))
        shadow_depth = max(1.5, round(font_size * 0.04, 1))
    else:
        # Standard horizontal 16:9 layout
        res_x = v_width
        res_y = v_height
        # Subtitle font ~7.5% of video height (big, bold, highly legible)
        font_size = int(res_y * 0.075)
        alignment = style_cfg.get("alignment", 2)
        margin_v = int(res_y * 0.10)                     # ~10% above bottom edge
        outline_width = max(3.5, round(font_size * 0.10, 1))
        shadow_depth = max(1.8, round(font_size * 0.04, 1))

    highlight_color = emph_cfg.get("highlight_color", "&H002BF7F7") # Bright yellow/gold
    highlight_bold = emph_cfg.get("highlight_bold", True)
    bold_all = emph_cfg.get("bold_all", False)
    emphasis_enabled = emph_cfg.get("enabled", True)

    words = transcribe_audio_words(video_path, model_size=model_size, language=language)
    if not words:
        print("[Subtitles] Warning: No spoken words detected in audio.")
        return None, None

    chunks = group_words_into_lines(words, max_words=max_words)
    print(f"[Subtitles] Generated {len(chunks)} subtitle display lines ({'9:16 Vertical' if is_short else '16:9 Horizontal'}).")

    # Build ASS Header
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,{"-1" if bold_all else "0"},0,0,0,100,100,0,0,1,{outline_width},{shadow_depth},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    ass_events = []
    srt_events = []

    for idx, chunk in enumerate(chunks, start=1):
        line_start = chunk[0]["start"]
        line_end = chunk[-1]["end"]

        # Ensure minimal display duration (at least 0.4s)
        if line_end - line_start < 0.4:
            line_end = line_start + 0.4

        # Clean words and find candidates for emphasis
        clean_words = [re.sub(r"[^\w$%]", "", w["word"]) for w in chunk]
        longest_len = max((len(c) for c in clean_words), default=0)

        styled_words = []
        raw_words = []

        for w, c_word in zip(chunk, clean_words):
            raw_text = w["word"]
            raw_words.append(raw_text)

            is_long = (len(c_word) == longest_len and longest_len >= 6)
            if emphasis_enabled and is_emphasis_word(c_word, is_longest=is_long):
                # Apply bold + vivid highlight color
                bold_tag = r"{\b1}" if highlight_bold else ""
                unbold_tag = r"{\b0}" if (highlight_bold and not bold_all) else ""
                styled = f"{bold_tag}{{\\c{highlight_color}&}}{raw_text}{{\\c{primary_color}&}}{unbold_tag}"
                styled_words.append(styled)
            else:
                styled_words.append(raw_text)

        ass_text = " ".join(styled_words)
        plain_text = " ".join(raw_words)

        ass_events.append(f"Dialogue: 0,{format_ass_time(line_start)},{format_ass_time(line_end)},Default,,0,0,0,,{ass_text}")

        srt_events.append(f"{idx}\n{format_srt_time(line_start)} --> {format_srt_time(line_end)}\n{plain_text}\n")

    # Write ASS file
    Path(output_ass_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(ass_events))
    print(f"[Subtitles] Saved stylized ASS subtitles to: {output_ass_path}")

    # Write SRT file
    if output_srt_path:
        Path(output_srt_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_events))
        print(f"[Subtitles] Saved plain SRT subtitles to: {output_srt_path}")

    # Write Plain-text Transcript
    if output_txt_path:
        Path(output_txt_path).parent.mkdir(parents=True, exist_ok=True)
        full_transcript = " ".join(" ".join(w["word"] for w in chunk) for chunk in chunks)
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(full_transcript + "\n")
        print(f"[Subtitles] Saved plain transcript to: {output_txt_path}")

    return output_ass_path, output_srt_path

def burn_subtitles_into_video(input_video, ass_subtitle_path, output_video):
    """
    Burns ASS subtitles directly into the video frames using ffmpeg's libass engine.
    """
    ffmpeg_exe, _ = get_ffmpeg_paths()
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    # Windows ffmpeg subtitle path formatting: forward slashes and escape colon
    clean_ass_path = str(Path(ass_subtitle_path).resolve()).replace("\\", "/")
    # Escape colon for ffmpeg filter: C:/ -> C\:/
    if ":" in clean_ass_path:
        drive, rest = clean_ass_path.split(":", 1)
        escaped_ass = f"{drive}\\:{rest}"
    else:
        escaped_ass = clean_ass_path

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_video),
        "-vf", f"subtitles=filename='{escaped_ass}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        str(output_video)
    ]

    print(f"[Subtitles] Burning subtitles into video: {Path(output_video).name}...")
    run_command(cmd)
    print("[Subtitles] Subtitles successfully burned in.")
    return output_video

def generate_shorts_crop(input_video, output_video, ass_subtitle_path=None):
    """
    Center-crops horizontal video to 9:16 vertical ratio and optionally burns subtitles.
    """
    ffmpeg_exe, _ = get_ffmpeg_paths()
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    filter_chain = "crop=ih*9/16:ih:(iw-ow)/2:0"
    if ass_subtitle_path and Path(ass_subtitle_path).exists():
        clean_ass_path = str(Path(ass_subtitle_path).resolve()).replace("\\", "/")
        if ":" in clean_ass_path:
            drive, rest = clean_ass_path.split(":", 1)
            escaped_ass = f"{drive}\\:{rest}"
        else:
            escaped_ass = clean_ass_path
        filter_chain += f",subtitles=filename='{escaped_ass}'"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_video),
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        str(output_video)
    ]

    print(f"[Shorts] Generating 9:16 vertical video: {Path(output_video).name}...")
    run_command(cmd)
    print("[Shorts] 9:16 Shorts export completed.")
    return output_video

