import srt

import os
import subprocess
from srtmerge import srtmerge


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

    subprocess.run(command)

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


if __name__ == "__main__":
    print("processing for all media file in current dir...")
    primary_sub_conf = {
        "track_num": 2,
        "lang_code": "eng",
    }
    secondary_sub_conf = {
        "track_num": 3,
        "lang_code": "chi"
    }
    target_dir = os.getcwd()
    tmp_dir = "/tmp/"
    output_dir = os.getcwd()
    media_files = os.listdir(target_dir)
    for media in media_files:
        if not media.endswith("mkv"):
            continue
        srt_a = extract_subtitles(media, primary_sub_conf["track_num"], primary_sub_conf["lang_code"], tmp_dir)
        srt_b = extract_subtitles(media, secondary_sub_conf["track_num"], secondary_sub_conf["lang_code"], tmp_dir)
        replace_newlines_with_spaces(srt_a)
        replace_newlines_with_spaces(srt_b)

        out = srt_merge(srt_a, srt_b, media, output_dir)

        print(f"done {out}")
