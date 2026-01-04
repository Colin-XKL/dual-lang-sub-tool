import os
import pytest
import shutil
import srt_tool.main as app
from unittest.mock import MagicMock, patch
import yaml

# --- Unit Tests ---

def test_match_track():
    tracks = [
        {'index': 0, 'language': 'chi', 'title': 'Chinese'},
        {'index': 1, 'language': 'eng', 'title': 'English'},
        {'index': 2, 'language': 'jpn', 'title': 'Japanese'}
    ]

    # Test exact/mapped matches
    assert app.match_track(tracks, 'zh') == 0
    assert app.match_track(tracks, 'en') == 1
    assert app.match_track(tracks, 'ja') == 2

    # Test unknown language
    assert app.match_track(tracks, 'fr') is None

def test_get_video_tracks_no_file():
    tracks = app.get_video_tracks("non_existent_file.mkv")
    assert tracks == []

# --- Integration Tests ---

def test_get_video_tracks_integration(generate_media_files):
    # Test MKV with chi/eng
    mkv_path = generate_media_files / "test_zh_en.mkv"
    tracks = app.get_video_tracks(str(mkv_path))

    # Depending on ffmpeg version and stream mapping, indices might vary.
    # We added video stream (index 0), audio? no audio in command.
    # So subtitle streams should be 1 and 2? Wait, -map 0:v is stream 0.
    # Subtitles are mapped as map 1 (input 1) and map 2 (input 2).
    # FFprobe will list them.

    langs = [t['language'] for t in tracks]
    assert 'chi' in langs
    assert 'eng' in langs

    # Test MP4 with jpn/kor
    mp4_path = generate_media_files / "test_ja_ko.mp4"
    tracks = app.get_video_tracks(str(mp4_path))
    langs = [t['language'] for t in tracks]
    assert 'jpn' in langs
    assert 'kor' in langs

def test_auto_mode_integration(generate_media_files, monkeypatch, capsys):
    # Setup working directory to be the temp path where media files are
    os.chdir(generate_media_files)

    # Test processing zh,en on mkv
    # The run_auto_mode function scans current directory
    app.run_auto_mode("zh,en")

    # Check if merged file exists
    merged_file = generate_media_files / "test_zh_en.srt"
    assert merged_file.exists()

    # Check content
    with open(merged_file, 'r') as f:
        content = f.read()
        assert "Chinese" in content
        assert "English" in content

    # Test processing ja,ko on mp4
    app.run_auto_mode("ja,ko")
    merged_file_mp4 = generate_media_files / "test_ja_ko.srt"
    assert merged_file_mp4.exists()

    with open(merged_file_mp4, 'r') as f:
        content = f.read()
        assert "Japanese" in content
        assert "Korean" in content

def test_auto_mode_missing_lang(generate_media_files, capsys):
    os.chdir(generate_media_files)

    # Request language that doesn't exist
    app.run_auto_mode("fr,de")

    captured = capsys.readouterr()
    assert "Could not find track for language 'fr'" in captured.out

    # Ensure no file is created for the missing one
    assert not (generate_media_files / "test_zh_en.srt").exists()

def test_legacy_mode_integration(generate_media_files, capsys):
    # Setup config file
    config_data = {
        'first_line_sub': {'track_num': 0, 'lang_code': 'chi'}, # track_num needs to be the ffmpeg stream index
        'sencond_line_sub': {'track_num': 1, 'lang_code': 'eng'},
        'file_extensions': ['mkv']
    }

    # In our generated MKV:
    # Stream 0: Video
    # Stream 1: Subtitle (chi)
    # Stream 2: Subtitle (eng)

    # Legacy mode uses extract_subtitles which passes track_num to -map 0:{track_num}
    # So we need to specify 1 and 2.

    config_data['first_line_sub']['track_num'] = 1
    config_data['sencond_line_sub']['track_num'] = 2

    with open(generate_media_files / "dual_sub_conf.yaml", "w") as f:
        yaml.dump(config_data, f)

    # Mock args
    class Args:
        target_dir = str(generate_media_files)
        check = False

    app.run_legacy_mode(Args())

    merged_file = generate_media_files / "test_zh_en.srt"
    assert merged_file.exists()

    with open(merged_file, 'r') as f:
        content = f.read()
        assert "Chinese" in content
        assert "English" in content

def test_check_mode(generate_media_files, capsys):
    class Args:
        target_dir = str(generate_media_files)
        check = True

    # We need to make sure there is a conf file or it handles missing conf (Legacy mode code checks conf existence unless check is True? No, checks conf if exists, else prints not found unless check.)
    # Let's see run_legacy_mode logic:
    # if os.path.exists(config_path): ...
    # elif not args.check: exit(1)

    # So if check=True, it proceeds even if config missing.

    try:
        app.run_legacy_mode(Args())
    except SystemExit as e:
        assert e.code == 0

    # Check mode runs ffmpeg -i on a random file.
    # Since we have files, it should print info.
    # We can check if ffmpeg was run (via capsys stderr/stdout if we allow it, but subprocess prints directly).
    # Since we can't easily capture subprocess output without mocking,
    # we just ensure it didn't crash (exit 0).
