import srt
import os
import subprocess
import sys
import argparse
import yaml
import random
import json
import tempfile
import collections
import collections.abc

# Monkeypatch for srtmerge
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable

from srtmerge import srtmerge


default_whitelist_extension_list = ["mkv", "mp4"]

def replace_newlines_with_spaces(file_path):
    # Read the SRT file
    with open(file_path, 'r') as file:
        srt_content = file.read()

    # Parse the SRT content
    subs = list(srt.parse(srt_content))

    # Replace newlines with spaces in each subtitle
    for sub in subs:
        sub.content = sub.content.replace('\n', ' ').replace("\n", " ").replace("\t", " ").replace("  ", " ").strip()

    # Generate the modified SRT content
    modified_srt_content = srt.compose(subs)

    # Write the modified SRT content back to the file
    with open(file_path, 'w') as file:
        file.write(modified_srt_content)


def extract_subtitles(input_file_path, track_num: int, lang_code: str, output_dir: str):
    input_file_path = os.path.abspath(input_file_path)
    base_file_name = get_base_name_without_ext(input_file_path)
    output_file_name = f"{base_file_name}.{lang_code}.srt"
    output_path = os.path.join(output_dir, output_file_name)

    # Run ffmpeg command to extract subtitles at Stream 0:track_num
    # Note: track_num passed here usually refers to the global stream index if obtained from ffprobe "index"
    # or a relative subtitle index if used with -map 0:s:index.
    # The existing code uses -map 0:track_num, so it expects global stream index.

    command = [
        "ffmpeg",
        "-i", input_file_path,
        "-map", f"0:{track_num}",
        "-c:s", "srt",
        "-y",  # Overwrite output file if it already exists
        output_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error executing ffmpeg command for {input_file_path}: {e}")
        return None

    return output_path


def get_base_name_without_ext(input_file) -> str:
    from pathlib import Path
    name = Path(input_file).stem
    return name


def srt_merge(srt_a, srt_b, media_name, output_dir: str):
    base_file_name = get_base_name_without_ext(media_name)
    output_file_name = f"{base_file_name}.srt"
    output_file_path = os.path.join(output_dir, output_file_name)

    srtmerge([srt_a, srt_b], output_file_path)
    return output_file_path


def get_video_tracks(filepath):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return []

    tracks = []
    if 'streams' not in data:
        return []

    for stream in data['streams']:
        if stream.get('codec_type') == 'subtitle':
            tags = stream.get('tags', {})
            # Normalized language handling could go here, but raw is fine for now
            lang = tags.get('language', 'unknown')
            tracks.append({
                'index': stream['index'], # Global index
                'language': lang,
                'title': tags.get('title', '')
            })
    return tracks

LANG_MAP = {
    'zh': ['chi', 'zho', 'zh', 'cmn', 'chn'],
    'en': ['eng', 'en'],
    'ja': ['jpn', 'ja', 'jp'],
    'ko': ['kor', 'ko'],
    'fr': ['fre', 'fra', 'fr'],
    'de': ['ger', 'deu', 'de'],
    'es': ['spa', 'es']
}

def match_track(tracks, req_lang):
    # Try exact match or mapped match
    candidates = LANG_MAP.get(req_lang, [req_lang])

    for t in tracks:
        t_lang = t['language'].lower()
        if t_lang in candidates:
            return t['index']

    return None

def run_auto_mode(lang_str):
    langs = lang_str.split(',')
    if len(langs) < 2:
        print("Warning: Only one language specified. Merging usually requires two.")

    target_dir = "."
    files = [f for f in os.listdir(target_dir) if any(f.endswith(ext) for ext in default_whitelist_extension_list)]

    if not files:
        print("No video files found in current directory.")
        return

    # Use a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Found {len(files)} video files. Processing...")

        for media in files:
            print(f"Analyzing {media}...")
            tracks = get_video_tracks(media)
            if not tracks:
                print(f"  No subtitle tracks found in {media}.")
                continue

            # Find tracks for requested languages
            found_tracks = []
            missing = False
            for lang in langs:
                idx = match_track(tracks, lang)
                if idx is not None:
                    found_tracks.append((lang, idx))
                else:
                    print(f"  Could not find track for language '{lang}' in {media}.")
                    missing = True
                    break

            if missing:
                continue

            # Extract tracks
            extracted_srts = []
            for lang, idx in found_tracks:
                srt_path = extract_subtitles(media, idx, lang, tmp_dir)
                if srt_path:
                    replace_newlines_with_spaces(srt_path)
                    extracted_srts.append(srt_path)
                else:
                    print(f"  Failed to extract subtitle for {lang}.")
                    missing = True
                    break

            if missing or len(extracted_srts) < 2:
                continue

            # Merge (currently only supports merging 2, if more, we might need loop)
            # srtmerge usually takes a list. Let's assume user provides 2 langs mostly.
            # But if more, srtmerge takes list of files.

            # The existing srt_merge function takes srt_a and srt_b.
            # Let's check srtmerge signature or usage.
            # srtmerge([srt_a, srt_b], output)

            if len(extracted_srts) == 2:
                out = srt_merge(extracted_srts[0], extracted_srts[1], media, target_dir)
                print(f"  Done: {out}")
            else:
                # If srtmerge supports more than 2, we can adapt srt_merge function
                # But the prompt says "merge chinese and english", implying 2.
                # If user provides more, maybe we should warn or try to merge all?
                # srtmerge library likely supports multiple.

                base_file_name = get_base_name_without_ext(media)
                output_file_name = f"{base_file_name}.srt"
                output_file_path = os.path.join(target_dir, output_file_name)

                try:
                    srtmerge(extracted_srts, output_file_path)
                    print(f"  Done: {output_file_path}")
                except Exception as e:
                    print(f"  Error merging subtitles: {e}")
def run_legacy_mode(args):
    config_path = os.path.join(args.target_dir, "dual_sub_conf.yaml")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(f"Error reading YAML file: {exc}")
            exit(1)
    elif not args.check:
        print(f"Config file not found: {config_path}")
        exit(1)

    file_extensions = config.get('file_extensions', default_whitelist_extension_list) if config else default_whitelist_extension_list

    if args.check:
        try:
            media_files = [f for f in os.listdir(args.target_dir) if any(f.endswith(ext) for ext in file_extensions)]
        except FileNotFoundError:
            print(f"Target directory not found: {args.target_dir}")
            exit(1)

        if not media_files:
            print("No media files found in the target directory.")
            exit(1)
        random_media = random.choice(media_files)
        random_media_path = os.path.join(args.target_dir, random_media)

        subprocess.run(["ffmpeg", "-i", random_media_path], check=False)
        exit(0)

    primary_sub_conf =config.get('first_line_sub')
    secondary_sub_conf = config.get('sencond_line_sub')
    if not primary_sub_conf or not secondary_sub_conf:
        print("Missing 'first_line_sub' or 'sencond_line_sub' in the YAML file.")
        exit(1)
    
    print(f"processing for all media file in [{args.target_dir}]  ...")
    target_dir = args.target_dir
    output_dir = target_dir

    with tempfile.TemporaryDirectory() as tmp_dir:
        media_files = os.listdir(target_dir)
        for media in media_files:
            if not any(media.endswith(ext) for ext in file_extensions):
                continue
            media_path = os.path.join(target_dir, media)
            srt_a = extract_subtitles(media_path, primary_sub_conf["track_num"], primary_sub_conf["lang_code"], tmp_dir)
            srt_b = extract_subtitles(media_path, secondary_sub_conf["track_num"], secondary_sub_conf["lang_code"], tmp_dir)

            if srt_a: replace_newlines_with_spaces(srt_a)
            if srt_b: replace_newlines_with_spaces(srt_b)

            if srt_a and srt_b:
                out = srt_merge(srt_a, srt_b, media, output_dir)
                print(f"done {out}")


def main():
    # Check if the first argument is 'auto'
    if len(sys.argv) > 1 and sys.argv[1] == 'auto':
        parser = argparse.ArgumentParser(description="Auto detect and merge subtitles.")
        parser.add_argument("command", choices=["auto"], help="Auto mode command")
        parser.add_argument("--lang", required=True, help="Languages to extract, e.g., zh,en")
        args = parser.parse_args()

        run_auto_mode(args.lang)
    else:
        parser = argparse.ArgumentParser(description="Process media files in a specified directory.")
        parser.add_argument("target_dir", type=str, help="Directory containing media files to process.")
        parser.add_argument("--check", action="store_true", help="Check a random media file in the target directory.")
        args = parser.parse_args()

        run_legacy_mode(args)

if __name__ == "__main__":
    main()
