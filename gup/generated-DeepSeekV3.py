import json
import os
import subprocess
from pathlib import Path

# 定义输入文件和输出目录
video_file = "PV01.mkv"
audio_file = "PV01.mka"
subtitles_dir = Path("dist/subsetted")
output_dir = Path("dist")
output_file = output_dir / "PV01_merged.mkv"

# 确保输出目录存在
output_dir.mkdir(parents=True, exist_ok=True)

# 构建mkvmerge命令
command = ["mkvmerge", "-o", str(output_file), str(video_file)]

# 添加音频文件（如果存在）
if os.path.exists(audio_file):
    command.append(str(audio_file))

# 添加字幕文件
sub_tracks = list(subtitles_dir.glob("PV01.*.ass"))
default_sub_index = None
for i, sub_file in enumerate(sub_tracks):
    lang_code = sub_file.stem.split(".")[1]
    if lang_code == "comment":
        track_name = "监督评论"
        lang = "und"
    else:
        if lang_code in ["sc", "SC"]:
            lang = "chi"
            track_name = "简体中文"
            if default_sub_index is None:  # 第一个简体中文轨道设为默认
                default_sub_index = i
        elif lang_code in ["tc", "TC"]:
            lang = "chi"
            track_name = "繁体中文"
        elif lang_code == "ja":
            lang = "jpn"
            track_name = "日文"
        else:
            lang = "chi"
            track_name = "简体中文"
    command.extend(
        ["--track-name", f"0:{track_name}", "--language", f"0:{lang}", str(sub_file)]
    )

# 设置默认字幕轨道
if len(sub_tracks) == 1:
    command.extend(["--default-track", "0:yes"])
elif len(sub_tracks) > 1 and default_sub_index is not None:
    command.extend(["--default-track", f"{default_sub_index}:yes"])

# 添加字体文件
font_files = (
    list(subtitles_dir.glob("*.[oO][tT][fF]"))
    + list(subtitles_dir.glob("*.[tT][tT][fF]"))
    + list(subtitles_dir.glob("*.[tT][tT][cC]"))
)
for font_file in font_files:
    command.extend(
        [
            "--attachment-mime-type",
            "application/x-truetype-font",
            "--attach-file",
            str(font_file),
        ]
    )

# 执行mkvmerge命令
print(" ".join(command))
subprocess.run(command)


# 使用mkvmerge -J获取文件信息
def get_track_info(mkv_file):
    """使用mkvmerge -J获取轨道信息"""
    info_command = ["mkvmerge", "-J", str(mkv_file)]
    result = subprocess.run(info_command, capture_output=True, text=True)
    return json.loads(result.stdout)


track_info = get_track_info(output_file)

# 重命名音频轨道
audio_tracks = []
for track in track_info.get("tracks", []):
    if track.get("type") == "audio":
        audio_tracks.append(
            {
                "id": track.get("id"),
                "codec": track.get("codec"),
                "channels": track.get("properties", {}).get("audio_channels", 0),
                "name": track.get("properties", {}).get("track_name"),
            }
        )

# 重命名FLAC音频轨道
for track in audio_tracks:
    if not track.get("name"):
        channels = track.get("channels", 0)
        if channels == 2:
            track_name = "2ch"
        elif channels == 3:
            track_name = "2.1ch"
        elif channels == 6:
            track_name = "5.1ch"
        else:
            track_name = f"{channels}ch"
        command = [
            "mkvpropedit",
            str(output_file),
            "--edit",
            f"track:a{track['id']}",
            "--set",
            f"name={track_name}",
        ]
        subprocess.run(command)

# 重命名AAC音频轨道
aac_tracks = [
    track
    for track in audio_tracks
    if track.get("codec") == "AAC" and not track.get("name")
]
for i, track in enumerate(aac_tracks):
    if i == 0:
        track_name = "声优评论"
    elif i == 1:
        track_name = "监督评论"
    elif i == 2:
        track_name = "军事评论"
    else:
        track_name = f"AAC Track {i + 1}"
    command = [
        "mkvpropedit",
        str(output_file),
        "--edit",
        f"track:a{track['id']}",
        "--set",
        f"name={track_name}",
    ]
    subprocess.run(command)
