import json
import os
import subprocess


def get_track_info(file_path):
    result = subprocess.run(
        ["mkvmerge", "-J", file_path], capture_output=True, text=True
    )
    return json.loads(result.stdout)


def get_channel_count(track):
    channels = track.get("properties", {}).get("audio_channels", 2)
    return channels


def process_subtitle_language(filename):
    parts = filename.split(".")
    if len(parts) < 3:
        return "zh-CN", "简体中文"

    lang_part = parts[1].lower()
    if lang_part == "comment":
        return "zh-CN", "监督评论"
    elif lang_part == "ja":
        return "ja", "日本語"
    elif lang_part == "sc":
        return "zh-CN", "简体中文"
    elif lang_part == "tc":
        return "zh-TW", "繁體中文"
    else:
        raise ValueError(f"{lang_part} 语言暂时无法处理")


def main():
    video_file = "PV01.mkv"
    audio_file = "PV01.mka"
    output_file = "dist/PV01.mkv"
    subtitle_dir = "dist/subsetted"

    # Create dist directory if it doesn't exist
    os.makedirs("dist", exist_ok=True)

    # Base command
    cmd = ["mkvmerge", "-o", output_file]

    # Handle video file
    get_track_info(video_file)
    cmd.extend([video_file])

    # Handle audio file if exists
    audio_tracks = []
    if os.path.exists(audio_file):
        audio_info = get_track_info(audio_file)
        audio_tracks.extend(audio_info["tracks"])
        cmd.extend(["+", audio_file])

    # Handle subtitles
    subtitle_files = [
        f
        for f in os.listdir(subtitle_dir)
        if f.startswith("PV01") and f.endswith(".ass")
    ]
    font_files = [
        f
        for f in os.listdir(subtitle_dir)
        if f.lower().endswith((".otf", ".ttf", ".ttc"))
    ]

    subtitle_langs = []
    for sub_file in subtitle_files:
        lang_code, track_name = process_subtitle_language(sub_file)
        cmd.extend(["--language", f"0:{lang_code}", "--sub-charset", "0:UTF-8"])
        cmd.extend(["--track-name", f"0:{track_name}"])
        cmd.append(os.path.join(subtitle_dir, sub_file))
        subtitle_langs.append((lang_code, track_name))

    # Handle fonts
    if font_files:
        cmd.append("--attachment-mime-type")
        cmd.append("application/x-truetype-font")
        for font in font_files:
            cmd.extend(["--attach-file", os.path.join(subtitle_dir, font)])

    # Execute mkvmerge
    print(cmd)
    subprocess.run(cmd, check=True)

    # Post-processing with mkvpropedit
    output_info = get_track_info(output_file)
    prop_cmd = ["mkvpropedit", output_file]

    # Handle subtitle defaults
    subtitle_tracks = [t for t in output_info["tracks"] if t["type"] == "subtitles"]
    if len(subtitle_tracks) == 1:
        prop_cmd.extend(["--edit", "track:s1", "--set", "flag-default=1"])
    elif len(subtitle_tracks) > 1:
        for i, track in enumerate(subtitle_tracks, 1):
            props = track["properties"]
            if (
                props.get("language") == "chi"
                and props.get("language_ietf") == "zh-CN"
                and "监督评论" not in props.get("track_name", "")
            ):
                prop_cmd.extend(["--edit", f"track:s{i}", "--set", "flag-default=1"])
            else:
                prop_cmd.extend(["--edit", f"track:s{i}", "--set", "flag-default=0"])

    # Handle audio tracks
    audio_tracks = [t for t in output_info["tracks"] if t["type"] == "audio"]
    if audio_tracks:
        # Find track with most channels
        max_channels = max(get_channel_count(t) for t in audio_tracks)
        aac_count = 0

        for i, track in enumerate(audio_tracks, 1):
            props = track["properties"]
            codec = track["codec"].lower()
            channels = get_channel_count(track)
            orig_name = props.get("track_name")

            # Set default audio
            if channels == max_channels:
                prop_cmd.extend(["--edit", f"track:a{i}", "--set", "flag-default=1"])
            else:
                prop_cmd.extend(["--edit", f"track:a{i}", "--set", "flag-default=0"])

            # Rename tracks if no original name
            if not orig_name:
                if "flac" in codec:
                    if channels == 2:
                        name = "2ch"
                    elif channels == 3:
                        name = "2.1ch"
                    elif channels == 6:
                        name = "5.1ch"
                    prop_cmd.extend(["--edit", f"track:a{i}", "--set", f"name={name}"])
                elif "aac" in codec:
                    aac_count += 1
                    if aac_count == 1:
                        name = "声优评论"
                    elif aac_count == 2:
                        name = "监督评论"
                    elif aac_count == 3:
                        name = "军事评论"
                    prop_cmd.extend(["--edit", f"track:a{i}", "--set", f"name={name}"])

    # Execute mkvpropedit
    if len(prop_cmd) > 2:
        print(prop_cmd)
        subprocess.run(prop_cmd, check=True)


if __name__ == "__main__":
    main()
