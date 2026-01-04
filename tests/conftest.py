import pytest
import os
import subprocess
import srt
import datetime

@pytest.fixture
def generate_media_files(tmp_path):
    """
    Generates dummy media files with subtitle tracks in the given temporary directory.
    Returns the path to the directory containing the files.
    """

    # helper to create srt content
    def create_dummy_srt(content_text, filename):
        subs = [
            srt.Subtitle(index=1, start=datetime.timedelta(seconds=1), end=datetime.timedelta(seconds=2), content=f"{content_text} line 1"),
            srt.Subtitle(index=2, start=datetime.timedelta(seconds=3), end=datetime.timedelta(seconds=4), content=f"{content_text} line 2")
        ]
        with open(tmp_path / filename, "w") as f:
            f.write(srt.compose(subs))
        return tmp_path / filename

    # Create dummy srt files
    zh_srt = create_dummy_srt("Chinese", "zh.srt")
    en_srt = create_dummy_srt("English", "en.srt")
    ja_srt = create_dummy_srt("Japanese", "ja.srt")
    ko_srt = create_dummy_srt("Korean", "ko.srt")

    # 1. Create MKV with CHI and ENG subs
    # ffmpeg -f lavfi -i color=c=black:s=640x480:d=1 -i zh.srt -i en.srt -map 0:v -map 1 -map 2 -c:v libx264 -c:s srt -metadata:s:s:0 language=chi -metadata:s:s:1 language=eng test_zh_en.mkv
    mkv_path = tmp_path / "test_zh_en.mkv"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=640x480:d=1",
        "-i", str(zh_srt),
        "-i", str(en_srt),
        "-map", "0:v", "-map", "1", "-map", "2",
        "-c:v", "libx264", "-c:s", "srt",
        "-metadata:s:s:0", "language=chi",
        "-metadata:s:s:1", "language=eng",
        str(mkv_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2. Create MP4 with JPN and KOR subs (MP4 usually uses mov_text for subs but ffmpeg can embed srt as distinct stream sometimes,
    # but strictly speaking MP4 container support for SRT is limited/specific.
    # However, existing code uses '-c:s srt' for extraction, so it expects srt-compatible streams.
    # FFmpeg can mux srt into mp4 (as text stream).
    mp4_path = tmp_path / "test_ja_ko.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=640x480:d=1",
        "-i", str(ja_srt),
        "-i", str(ko_srt),
        "-map", "0:v", "-map", "1", "-map", "2",
        "-c:v", "libx264", "-c:s", "mov_text", # MP4 standard usually requires mov_text
        "-metadata:s:s:0", "language=jpn",
        "-metadata:s:s:1", "language=kor",
        str(mp4_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Note: If existing code tries to extract 'srt' from 'mov_text', ffmpeg handles conversion automatically if -c:s srt is specified during extraction.

    # 3. Create file with no subs
    nosub_path = tmp_path / "test_nosubs.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=640x480:d=1",
        "-c:v", "libx264",
        str(nosub_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return tmp_path
