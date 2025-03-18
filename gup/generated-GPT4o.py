import json
import os
import re
import subprocess


def extract_tracks_with_mediainfo(file, track_type):
    """Extract detailed track information from MediaInfo."""
    result = subprocess.run(
        ["mediainfo", "--Output=JSON", file], capture_output=True, text=True
    )
    mediainfo = json.loads(result.stdout)

    tracks = []
    for track in mediainfo["media"]["track"]:
        if track["@type"].lower() == track_type.lower():
            track_info = {
                "id": track["StreamOrder"],
                "codec": track.get("Format", ""),
                "channels": track.get("Channels", ""),  # For audio only
                "language": track.get("Language", ""),  # For subtitles
                "title": track.get("Title", ""),  # Title of the track
            }
            tracks.append(track_info)

    return tracks


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

    # Post-process: Extract information using MediaInfo
    audio_details = extract_tracks_with_mediainfo(output_file, "audio")
    subtitle_details = extract_tracks_with_mediainfo(
        output_file, "text"
    )  # "text" refers to subtitles

    # Rename audio tracks & set default audio
    if audio_details:
        default_audio_id = max(
            audio_details, key=lambda track: int(track.get("channels", 0))
        )["id"]  # Use the audio track with most channels as default

        for track in audio_details:
            track_id = int(track["id"]) + 1  # Adjust for Matroska's track indexing
            codec = track.get("codec", "Unknown")
            channels = track.get("channels", "")
            name = f"{codec} {channels}ch" if channels else codec

            # Set name
            subprocess.run(
                [
                    "mkvpropedit",
                    output_file,
                    "--edit",
                    f"track:a{track_id}",
                    "--set",
                    f"name={name}",
                ]
            )

            # Set default audio track
            is_default = track["id"] == default_audio_id
            subprocess.run(
                [
                    "mkvpropedit",
                    output_file,
                    "--edit",
                    f"track:a{track_id}",
                    "--set",
                    f"flag-default={'1' if is_default else '0'}",
                ]
            )

    # Set default subtitle track
    if subtitle_details:
        default_subtitle_id = None

        # Find Simplified Chinese first
        for track in subtitle_details:
            if track["language"] == "zh-CN":
                default_subtitle_id = track["id"]
                break

        # If no Simplified Chinese found, use the first subtitle track
        if default_subtitle_id is None:
            default_subtitle_id = subtitle_details[0]["id"]

        # Set or unset default flag
        for track in subtitle_details:
            track_id = int(track["id"]) + 1  # Adjust for Matroska's track indexing
            is_default = track["id"] == default_subtitle_id
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
