import os
import re
import subprocess


def remux_with_mkvtoolnix():
    video_file = "PV01.mkv"
    audio_file = "PV01.mka"
    dist_folder = "dist"
    subsetted_folder = os.path.join(dist_folder, "subsetted")
    output_file = os.path.join(dist_folder, "PV01_final.mkv")

    # Initialize arguments for mkvmerge
    args = ["mkvmerge", "-o", output_file, "--no-subtitles"]

    # Add video file
    args.extend(["--no-audio", video_file])

    # Collect existing subtitle tracks in the MKV and retain
    args.extend(["--no-audio", "--no-video", "--no-chapters", video_file])

    # Add external audio file if exists
    if os.path.exists(audio_file):
        args.extend(["--no-subtitles", audio_file])

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
            else:
                # Default to Simplified Chinese if no specific language code
                args.extend(
                    [
                        "--language",
                        "0:zh",
                        "--track-name",
                        "0:Simplified Chinese",
                        subtitle_file,
                    ]
                )

    # Add font attachments
    for font_file in font_files:
        # Ensure the attachment name in the output is unique
        attachment_name = os.path.basename(font_file)
        attachment_name += f"_{hash(font_file)}"  # Append hash to ensure uniqueness

        # Check if the file extension is valid (ttf, otf, ttc); otherwise, skip it
        if not re.search(r"\.(ttf|otf|ttc)$", font_file, re.IGNORECASE):
            print(f"Skipping unsupported font file: {font_file}")
            continue

        # Add font file as attachment with unique name
        args.extend(["--attachment-name", attachment_name, font_file])

    # Execute mkvmerge command to create the new file
    print(" ".join(args))
    subprocess.run(args)

    # Post-processing: Analyze and adjust default tracks and naming
    cmd_identify = ["mkvmerge", "-i", output_file]
    process = subprocess.run(cmd_identify, capture_output=True, text=True)
    output_info = process.stdout.splitlines()

    audio_tracks = []
    subtitle_tracks = []
    for line in output_info:
        if "audio" in line:
            audio_tracks.append(line)
        elif "subtitles" in line:
            subtitle_tracks.append(line)

    # Determine default audio track: Use the one with the highest number of channels
    audio_channels = {}
    for track in audio_tracks:
        match = re.search(r"Track ID (\d+): audio \((\w+), (\d+[.]?\d*)ch\)", track)
        if match:
            track_id = int(match.group(1))
            codec = match.group(2)
            channels = float(match.group(3))
            audio_channels[track_id] = {"codec": codec, "channels": channels}

    if audio_channels:
        default_audio_track = max(
            audio_channels, key=lambda k: audio_channels[k]["channels"]
        )
        # Set the default audio track
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

        # Rename FLAC audio tracks based on channels
        for track_id, track_data in audio_channels.items():
            if track_data["codec"] == "flac":
                ch_name = f"{track_data['channels']}ch"
                subprocess.run(
                    [
                        "mkvpropedit",
                        output_file,
                        "--edit",
                        f"track:a{track_id}",
                        "--set",
                        f"name={ch_name}",
                    ]
                )

        # Rename AAC audio tracks with specific commentary names
        aac_track_order = [
            "Voice Actors Commentary",
            "Director Commentary",
            "Military Commentary",
        ]
        aac_track_idx = 0
        for track_id, track_data in audio_channels.items():
            if track_data["codec"] == "aac" and aac_track_idx < len(aac_track_order):
                subprocess.run(
                    [
                        "mkvpropedit",
                        output_file,
                        "--edit",
                        f"track:a{track_id}",
                        "--set",
                        f"name={aac_track_order[aac_track_idx]}",
                    ]
                )
                aac_track_idx += 1

    # Determine the default subtitle track: Simplified Chinese takes priority
    default_subtitle_track = None
    for track in subtitle_tracks:
        match = re.search(
            r"Track ID (\d+): subtitles \(.*?, Simplified Chinese\)", track
        )
        if match:
            default_subtitle_track = int(match.group(1))
            break

    if default_subtitle_track is None and subtitle_tracks:
        # If no Simplified Chinese subtitle, choose the first subtitle as default
        match = re.search(r"Track ID (\d+): subtitles", subtitle_tracks[0])
        if match:
            default_subtitle_track = int(match.group(1))

    if default_subtitle_track is not None:
        # Set the default subtitle track
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
