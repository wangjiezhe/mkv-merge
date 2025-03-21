import json
import os
import subprocess
from itertools import chain
from pathlib import Path

# 定义输入文件和输出目录
video_file = "S01E01.mkv"
audio_file = Path(video_file).with_suffix(".mka").as_posix()
subtitles_dir = Path("dist/subsetted")
output_dir = Path("dist")
output_file = output_dir / f"{Path(video_file).stem}_merged.mkv"

# 确保输出目录存在
output_dir.mkdir(parents=True, exist_ok=True)

# 构建mkvmerge命令
command = ["mkvmerge", "-o", str(output_file), str(video_file)]

# 添加音频文件（如果存在）
if os.path.exists(audio_file):
    command.append(str(audio_file))

# 添加字幕文件
for sub_file in chain(
    subtitles_dir.glob("S01E01.ass"), subtitles_dir.glob("S01E01.*.ass")
):
    lang_code = sub_file.stem.split(".")[1].lower()
    if lang_code == "comment":
        track_name = "监督评论"
        lang = "zh-CN"
    else:
        if lang_code in ["sc", "chs"]:
            lang = "zh-CN"
            track_name = "简体中文"
        elif lang_code in ["tc", "cht"]:
            lang = "zh-TW"
            track_name = "繁体中文"
        elif lang_code == "ja":
            lang = "jpn"
            track_name = "日文"
        else:
            lang = "und"
            track_name = "未知语言"
    command.extend(
        ["--track-name", f"0:{track_name}", "--language", f"0:{lang}", str(sub_file)]
    )

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

# 单独修改默认字幕轨道设置
sub_track_ids = [
    track.get("id")
    for track in track_info.get("tracks", [])
    if track.get("type") == "subtitles"
]
if sub_track_ids:
    if len(sub_track_ids) == 1:
        # 如果只有一个字幕轨道，将其设为默认
        cmd = [
            "mkvpropedit",
            str(output_file),
            "--edit",
            "track:s1",
            "--set",
            "flag-default=1",
        ]
        print(" ".join(cmd))
        subprocess.run(cmd)
    elif len(sub_track_ids) > 1:
        # 如果有多个字幕轨道，找到第一个简体中文轨道并设为默认
        default_sub_index = None
        for i, track in enumerate(
            track
            for track in track_info.get("tracks", [])
            if track.get("type") == "subtitles"
        ):
            if (
                track.get("properties", {}).get("language") == "chi"
                and track.get("properties", {}).get("language_ietf") == "zh-CN"
            ):
                default_sub_index = i + 1  # 轨道序号从1开始
                break
        if default_sub_index:
            # 设置默认轨道
            cmd = [
                "mkvpropedit",
                str(output_file),
                "--edit",
                f"track:s{default_sub_index}",
                "--set",
                "flag-default=1",
            ]
            print(" ".join(cmd))
            subprocess.run(cmd)
            # 将其他字幕轨道设为非默认
            for i in range(1, len(sub_track_ids) + 1):  # 轨道序号从1开始
                if i != default_sub_index:
                    cmd = [
                        "mkvpropedit",
                        str(output_file),
                        "--edit",
                        f"track:s{i}",
                        "--set",
                        "flag-default=0",
                    ]
                    print(" ".join(cmd))
                    subprocess.run(cmd)

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
    if track.get("codec") == "FLAC" and not track.get("name"):
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
        print(" ".join(command))
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
    print(" ".join(command))
    subprocess.run(command)
