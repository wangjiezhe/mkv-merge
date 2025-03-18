import os
import re
import subprocess


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

    # Add subtitle files with proper language and naming
    for subtitle_file in subtitle_files:
        file_name = os.path.basename(subtitle_file)
        match = re.match(r"PV01\.(.*?)\.ass", file_name)
        if match:
            lang_code = match.group(1).lower()
            if lang_code in ["sc", "simplified", "简体中文"]:
                args.extend(
                    [
                        "--language",
                        "0:zh",
                        "--track-name",
                        "0:Simplified Chinese",
                        subtitle_file,
                    ]
                )
            elif lang_code in ["tc", "traditional", "繁体中文"]:
                args.extend(
                    [
                        "--language",
                        "0:zh-TW",
                        "--track-name",
                        "0:Traditional Chinese",
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
                        subtitle_file,
                    ]
                )
            elif lang_code == "comment":
                args.extend(
                    [
                        "--track-name",
                        "0:Director Commentary",
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
    print(" ".join(args))
    subprocess.run(args)

    # Post-process: Set appropriate default audio and subtitles
    cmd_identify = ["mkvmerge", "-i", output_file]
    process = subprocess.run(cmd_identify, capture_output=True, text=True)
    output_info = process.stdout.splitlines()

    # Set default audio track
    audio_tracks = {}
    for line in output_info:
        if "audio" in line:
            match = re.search(r"Track ID (\d+): audio \((\w+), (\d+[.]?\d*)ch\)", line)
            if match:
                track_id = int(match.group(1))
                codec = match.group(2)
                channels = float(match.group(3))
                audio_tracks[track_id] = {"codec": codec, "channels": channels}

    if audio_tracks:
        default_audio_track = max(
            audio_tracks, key=lambda k: audio_tracks[k]["channels"]
        )
        subprocess.run(
            [
                "mkvpropedit",
                output_file,
                "--edit",
                f"track:a{default_audio_track}",
                "--set",
                "flag-default=1",
            ]
        )

    # Set default subtitle track
    subtitle_tracks = []
    default_subtitle_track = None
    for line in output_info:
        if "subtitles" in line:
            subtitle_tracks.append(line)
            if "Simplified Chinese" in line or "zh" in line:
                match = re.search(r"Track ID (\d+):", line)
                if match:
                    default_subtitle_track = int(match.group(1))

    if default_subtitle_track is None and subtitle_tracks:
        match = re.search(r"Track ID (\d+):", subtitle_tracks[0])
        if match:
            default_subtitle_track = int(match.group(1))

    if default_subtitle_track is not None:
        subprocess.run(
            [
                "mkvpropedit",
                output_file,
                "--edit",
                f"track:s{default_subtitle_track}",
                "--set",
                "flag-default=1",
            ]
        )


if __name__ == "__main__":
    remux_with_mkvtoolnix()
