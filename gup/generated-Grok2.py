import os
import re
import subprocess


def get_language_name(code):
    language_names = {
        "ja": "日文",
        "sc": "简体中文",
        "SC": "简体中文",
        "tc": "繁体中文",
        "TC": "繁体中文",
        "comment": "监督评论",
    }
    return language_names.get(code, "简体中文")  # Default to 简体中文 if code not found


def get_audio_channel_name(channels):
    channel_names = {1: "1ch", 2: "2ch", 3: "2.1ch", 6: "5.1ch", 7: "6.1ch", 8: "7.1ch"}
    return channel_names.get(channels, f"{channels}ch")


def get_audio_track_info(track):
    channels = int(track["channels"])
    codec = track["codec"].lower()
    name = track["name"] if track["name"] else ""

    if codec == "flac" and not name:
        name = get_audio_channel_name(channels)
    elif codec == "aac" and not name:
        if track["number"] == 0:
            name = "声优评论"
        elif track["number"] == 1:
            name = "监督评论"
        elif track["number"] == 2:
            name = "军事评论"

    return {
        "number": track["number"],
        "codec": codec,
        "channels": channels,
        "name": name,
    }


def set_default_tracks(tracks):
    subtitles = [t for t in tracks if t["type"] == "subtitles"]
    audios = [t for t in tracks if t["type"] == "audio"]

    if len(subtitles) == 1:
        subtitles[0]["default"] = "yes"
    elif len(subtitles) > 1:
        for subtitle in subtitles:
            if subtitle["language"] in ["sc", "SC"] and subtitle["name"] != "监督评论":
                subtitle["default"] = "yes"
                break

    if audios:
        max_channels_audio = max(audios, key=lambda x: x["channels"])
        max_channels_audio["default"] = "yes"


def main():
    input_mkv = "PV01.mkv"
    input_mka = "PV01.mka"
    output_mkv = "dist/PV01.mkv"

    command = ["mkvmerge", "-o", output_mkv]

    # Add video tracks from input mkv
    command.extend(["-D", input_mkv])

    # Add audio tracks
    audio_tracks = []
    result = subprocess.run(
        ["mkvmerge", "--identify", input_mkv], capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        match = re.match(r"Track ID (\d+): audio \((\w+)\)", line)
        if match:
            track_id, codec = match.groups()
            result = subprocess.run(
                ["mkvmerge", "--identify", f"{input_mkv}:{track_id}"],
                capture_output=True,
                text=True,
            )
            channels = re.search(r"channels: (\d+)", result.stdout)
            name = re.search(r"track name: (.+)", result.stdout)
            audio_tracks.append(
                {
                    "number": len(audio_tracks),
                    "id": track_id,
                    "codec": codec,
                    "channels": int(channels.group(1)) if channels else 0,
                    "name": name.group(1) if name else "",
                }
            )

    if os.path.exists(input_mka):
        result = subprocess.run(
            ["mkvmerge", "--identify", input_mka], capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            match = re.match(r"Track ID (\d+): audio \((\w+)\)", line)
            if match:
                track_id, codec = match.groups()
                result = subprocess.run(
                    ["mkvmerge", "--identify", f"{input_mka}:{track_id}"],
                    capture_output=True,
                    text=True,
                )
                channels = re.search(r"channels: (\d+)", result.stdout)
                name = re.search(r"track name: (.+)", result.stdout)
                audio_tracks.append(
                    {
                        "number": len(audio_tracks),
                        "id": f"{input_mka}:{track_id}",
                        "codec": codec,
                        "channels": int(channels.group(1)) if channels else 0,
                        "name": name.group(1) if name else "",
                    }
                )

    for track in audio_tracks:
        info = get_audio_track_info(track)
        command.extend(
            ["--language", "0:und", "--track-name", f"0:{info['name']}", track["id"]]
        )

    # Add subtitle tracks
    subtitle_tracks = []
    subtitle_dir = "dist/subsetted"
    for file in os.listdir(subtitle_dir):
        if file.startswith("PV01.") and file.endswith(".ass"):
            parts = file.split(".")
            if len(parts) == 3:
                language = parts[1]
                name = get_language_name(language)
            else:
                language = "sc"
                name = "简体中文"

            command.extend(
                [
                    "--language",
                    "0:und",
                    "--track-name",
                    f"0:{name}",
                    os.path.join(subtitle_dir, file),
                ]
            )
            subtitle_tracks.append(
                {"number": len(subtitle_tracks), "language": language, "name": name}
            )

    # Add font attachments
    font_dir = "dist/subsetted"
    for file in os.listdir(font_dir):
        if file.lower().endswith((".otf", ".ttf", ".ttc")):
            command.extend(
                [
                    "--attachment-mime-type",
                    "application/x-truetype-font",
                    "--attach-file",
                    os.path.join(font_dir, file),
                ]
            )

    # Set default tracks
    tracks = audio_tracks + subtitle_tracks
    set_default_tracks(tracks)

    for track in tracks:
        if "default" in track and track["default"] == "yes":
            command.extend(["--default-track", f"{track['number']}:yes"])

    # Execute the command
    subprocess.run(command)


if __name__ == "__main__":
    main()
