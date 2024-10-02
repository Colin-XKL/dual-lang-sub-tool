import srt
import os
import subprocess
from srtmerge import srtmerge
import argparse
import yaml
import random


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


# Replace newlines with spaces in the example.srt file


def extract_subtitles(input_file_path, track_num: int, lang_code: str, output_dir: str):
    input_file_path = os.path.abspath(input_file_path)
    base_file_name = get_base_name_without_ext(input_file_path)
    output_file_name = f"{base_file_name}.{lang_code}.srt"
    output_path = os.path.join(output_dir, output_file_name)

    # Run ffmpeg command to extract English subtitles at Stream #0:3
    command = [
        "ffmpeg",
        "-i", input_file_path,
        "-map", f"0:{track_num}",
        "-c:s", "srt",
        "-y",  # Overwrite output file if it already exists
        output_path
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing ffmpeg command: {e}")
        exit(1)

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

default_whitelist_extension_list = ["mkv","mp4"]
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process media files in a specified directory.")
    parser.add_argument("target_dir", type=str, help="Directory containing media files to process.")
    parser.add_argument("--check", action="store_true", help="Check a random media file in the target directory.")
    args = parser.parse_args()

    config_path = os.path.join(args.target_dir, "dual_sub_conf.yaml")
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(f"Error reading YAML file: {exc}")
        exit(1)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        exit(1)

    primary_sub_conf =config.get('first_line_sub')
    secondary_sub_conf = config.get('sencond_line_sub')
    file_extensions = config.get('file_extensions', default_whitelist_extension_list)
    if not primary_sub_conf or not secondary_sub_conf:
        print("Missing 'first_line_sub' or 'sencond_line_sub' in the YAML file.")
        exit(1)

    if args.check:
        media_files = [f for f in os.listdir(args.target_dir) if any(f.endswith(ext) for ext in file_extensions)]
        if not media_files:
            print("No media files found in the target directory.")
            exit(1)
        random_media = random.choice(media_files)
        random_media_path = os.path.join(args.target_dir, random_media)

        subprocess.run(["ffmpeg", "-i", random_media_path], check=False)
        exit(0)

    print(f"processing for all media file in [{args.target_dir}]  ...")
    target_dir = args.target_dir
    tmp_dir = "/tmp/"
    output_dir = target_dir
    media_files = os.listdir(target_dir)
    for media in media_files:
        if not any(media.endswith(ext) for ext in file_extensions):
            continue
        media_path = os.path.join(target_dir, media)
        srt_a = extract_subtitles(media_path, primary_sub_conf["track_num"], primary_sub_conf["lang_code"], tmp_dir)
        srt_b = extract_subtitles(media_path, secondary_sub_conf["track_num"], secondary_sub_conf["lang_code"], tmp_dir)
        replace_newlines_with_spaces(srt_a)
        replace_newlines_with_spaces(srt_b)

        out = srt_merge(srt_a, srt_b, media, output_dir)

        print(f"done {out}")
