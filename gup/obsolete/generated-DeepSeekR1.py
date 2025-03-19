import glob
import json
import os
import subprocess


def get_track_info(file_path):
    cmd = ["mkvmerge", "-J", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def set_default_subtitle(output_file):
    info = get_track_info(output_file)
    if not info:
        return
    subtitles = []
    for track in info.get("tracks", []):
        if track.get("type") == "subtitles":
            language = track.get("properties", {}).get("language", "und")
            track_name = track.get("properties", {}).get("track_name", "")
            is_comment = "监督评论" in track_name
            subtitles.append(
                {"id": track["id"], "language": language, "is_comment": is_comment}
            )

    if not subtitles:
        return

    default_id = None
    if len(subtitles) == 1:
        default_id = subtitles[0]["id"]
    else:
        for sub in subtitles:
            if not sub["is_comment"] and sub["language"] in ["zho-CN", "chi-CN"]:
                default_id = sub["id"]
                break
        if not default_id:
            for sub in subtitles:
                if not sub["is_comment"]:
                    default_id = sub["id"]
                    break

    if default_id is not None:
        cmd = [
            "mkvpropedit",
            output_file,
            "--edit",
            f"track:@{default_id}",
            "--set",
            "default-track-flag=1",
        ]
        subprocess.run(cmd)


video_input = "PV01.mkv"
audio_input = "PV01.mka" if os.path.exists("PV01.mka") else None
subset_dir = os.path.join("dist", "subsetted")
output_dir = "dist"
output_file = os.path.join(output_dir, "PV01.mkv")

os.makedirs(output_dir, exist_ok=True)

subtitle_files = glob.glob(os.path.join(subset_dir, "PV01.*.ass"))
subtitle_options = []
for sub in subtitle_files:
    parts = os.path.basename(sub).split(".")
    if len(parts) < 3:
        continue
    lang_part = parts[1].lower()
    track_name = None
    language = None
    if lang_part == "comment":
        track_name = "监督评论"
    else:
        if lang_part == "ja":
            track_name = "Japanese"
            language = "jpn"
        elif lang_part == "sc":
            track_name = "Chinese (Simplified)"
            language = "zho-CN"
        elif lang_part == "tc":
            track_name = "Chinese (Traditional)"
            language = "zho-TW"
    options = []
    if language:
        options.extend(["--language", "0:" + language])
    if track_name:
        options.extend(["--track-name", "0:" + track_name])
    options.append(sub)
    subtitle_options.append(options)

font_files = []
for f in os.listdir(subset_dir):
    ext = os.path.splitext(f)[1]
    if ext:
        ext = ext[1:].lower()
        if ext in {"otf", "ttf", "ttc"}:
            font_files.append(os.path.join(subset_dir, f))

tracks = []
mkv_info = get_track_info(video_input)
if mkv_info:
    for track in mkv_info.get("tracks", []):
        if track.get("type") == "audio":
            tracks.append(
                {
                    "file": video_input,
                    "id": track["id"],
                    "codec": track.get("codec", ""),
                    "channels": track.get("properties", {}).get("audio_channels", 0),
                    "name": track.get("properties", {}).get("track_name", ""),
                }
            )

if audio_input and os.path.exists(audio_input):
    mka_info = get_track_info(audio_input)
    if mka_info:
        for track in mka_info.get("tracks", []):
            if track.get("type") == "audio":
                tracks.append(
                    {
                        "file": audio_input,
                        "id": track["id"],
                        "codec": track.get("codec", ""),
                        "channels": track.get("properties", {}).get(
                            "audio_channels", 0
                        ),
                        "name": track.get("properties", {}).get("track_name", ""),
                    }
                )

max_channels = max(track["channels"] for track in tracks) if tracks else 0
default_track = next((t for t in tracks if t["channels"] == max_channels), None)

command = ["mkvmerge", "-o", output_file]

# 处理视频文件轨道参数
video_params = [video_input]
if mkv_info:
    for track in mkv_info.get("tracks", []):
        if track["type"] == "audio":
            track_params = []
            is_default = track["id"] == default_track["id"] if default_track else False
            track_params.append(
                f"--default-track {track['id']}:{1 if is_default else 0}"
            )

            if not track.get("properties", {}).get("track_name"):
                if track["codec"].lower() == "flac":
                    name = f"{track['properties']['audio_channels']}ch"
                    track_params.append(f"--track-name {track['id']}:{name}")
                elif track["codec"].lower() == "aac":
                    name_map = {1: "声优评论", 2: "监督评论", 3: "军事评论"}
                    name = name_map.get(len(track_params) + 1)
                    if name:
                        track_params.append(f"--track-name {track['id']}:{name}")

            video_params.extend(track_params)
command.extend(video_params)

# 处理音频文件轨道参数
if audio_input:
    audio_params = [audio_input]
    if mka_info:
        for track in mka_info.get("tracks", []):
            if track["type"] == "audio":
                track_params = []
                is_default = (
                    track["id"] == default_track["id"] if default_track else False
                )
                track_params.append(
                    f"--default-track {track['id']}:{1 if is_default else 0}"
                )

                if not track.get("properties", {}).get("track_name"):
                    if track["codec"].lower() == "flac":
                        name = f"{track['properties']['audio_channels']}ch"
                        track_params.append(f"--track-name {track['id']}:{name}")
                    elif track["codec"].lower() == "aac":
                        name_map = {1: "声优评论", 2: "监督评论", 3: "军事评论"}
                        name = name_map.get(len(track_params) + 1)
                        if name:
                            track_params.append(f"--track-name {track['id']}:{name}")

                audio_params.extend(track_params)
    command.extend(audio_params)

# 添加字幕
for opts in subtitle_options:
    command.extend(opts)

# 添加字体
for font in font_files:
    command.extend(["--attach-file", font])

print(" ".join(command))
subprocess.run(command)
set_default_subtitle(output_file)
