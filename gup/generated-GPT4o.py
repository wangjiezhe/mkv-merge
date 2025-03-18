import json
import os
import re
import subprocess


def extract_audio_tracks_with_mediainfo(file):
    """Extract detailed audio track information using MediaInfo."""
    result = subprocess.run(
        ["mediainfo", "--Output=JSON", file], capture_output=True, text=True
    )
    mediainfo = json.loads(result.stdout)

    audio_tracks = []
    for track in mediainfo["media"]["track"]:
        if track["@type"] == "Audio":
            audio_info = {
                "codec": track.get("Format", ""),
                "channels": track.get("Channel(s)", ""),
                "track_id": track.get(
                    "StreamOrder", ""
                ),  # Note: Mapping with mkvmerge IDs may be needed
            }
            audio_tracks.append(audio_info)

    return audio_tracks


def remux_with_mkvtoolnix():
    video_file = "PV01.mkv"
    audio_file = "PV01.mka"
    dist_folder = "dist"
    subsetted_folder = os.path.join(dist_folder, "subsetted")
    output_file = os.path.join(dist_folder, "PV01_final.mkv")

    args = ["mkvmerge", "-o", output_file]

    # Add video and retain its audio tracks
    args.append(video_file)

    # Add external audio file if exists
    if os.path.exists(audio_file):
        args.append(audio_file)

    # Collect subtitle and font files
    subtitle_files = []
    font_files = []
    for f in os.listdir(subsetted_folder):
        filepath = os.path.join(subsetted_folder, f)
        if re.match(r"PV01\..*\.ass", f):  # Subtitle file
            subtitle_files.append(filepath)
        elif re.match(r".*\.(ttf|otf|ttc)", f, re.IGNORECASE):  # Font file
            font_files.append(filepath)

    # Add subtitle files
    default_subtitle_track_found = False
    for subtitle_file in subtitle_files:
        file_name = os.path.basename(subtitle_file)
        match = re.match(r"PV01\.(.*?)\.ass", file_name)

        if match:
            lang_code = match.group(1).lower()
            if lang_code in ["sc", "simplified", "简体中文"]:
                args.extend(
                    [
                        "--language",
                        "0:zh-CN",
                        "--track-name",
                        "0:Simplified Chinese",
                        "--default-track",
                        "0:yes" if not default_subtitle_track_found else "0:no",
                        subtitle_file,
                    ]
                )
                default_subtitle_track_found = True
            elif lang_code in ["tc", "traditional", "繁体中文"]:
                args.extend(
                    [
                        "--language",
                        "0:zh-TW",
                        "--track-name",
                        "0:Traditional Chinese",
                        "--default-track",
                        "0:no",
                        subtitle_file,
                    ]
                )
            elif lang_code == "ja":
                args.extend(
                    [
                        "--language",
                        "0:ja",
                        "--track-name",
                        "0:Japanese",
                        "--default-track",
                        "0:no",
                        subtitle_file,
                    ]
                )
            elif lang_code == "comment":
                args.extend(
                    [
                        "--track-name",
                        "0:Director Commentary",
                        "--default-track",
                        "0:no",
                        subtitle_file,
                    ]
                )

    # Add font attachments
    for font_file in font_files:
        attachment_name = os.path.basename(font_file)
        if not re.search(r"\.(ttf|otf|ttc)$", font_file, re.IGNORECASE):
            print(f"Skipping unsupported font file: {font_file}")
            continue
        args.extend(["--attachment-name", attachment_name, "--attach-file", font_file])

    # Execute mkvmerge command to create the new file
    subprocess.run(args)

    # Post-process: Rename tracks using mediainfo and mkvpropedit
    audio_details = extract_audio_tracks_with_mediainfo(output_file)
    for i, track in enumerate(audio_details):
        codec = track.get("codec", "Unknown")
        channels = track.get("channels", "")
        name = f"{codec} {channels}ch" if channels else codec
        subprocess.run(
            [
                "mkvpropedit",
                output_file,
                "--edit",
                f"track:a{i}",
                "--set",
                f"name={name}",
            ]
        )

    # Ensure only one default subtitle track
    cmd_identify = ["mkvmerge", "-i", output_file]
    process = subprocess.run(cmd_identify, capture_output=True, text=True)
    output_info = process.stdout.splitlines()

    subtitle_tracks = {}
    for line in output_info:
        if "subtitles" in line:
            match = re.search(r"Track ID (\d+):", line)
            if match:
                track_id = int(match.group(1))
                subtitle_tracks[track_id] = line

    if subtitle_tracks:
        default_track_id = list(subtitle_tracks.keys())[
            0
        ]  # Use the first subtitle track as default
        for track_id in subtitle_tracks:
            is_default = track_id == default_track_id
            subprocess.run(
                [
                    "mkvpropedit",
                    output_file,
                    "--edit",
                    f"track:s{track_id}",
                    "--set",
                    f"flag-default={'1' if is_default else '0'}",
                ]
            )


if __name__ == "__main__":
    remux_with_mkvtoolnix()
