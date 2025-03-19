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
for sub_file in subtitles_dir.glob("PV01.*.ass"):
    lang_code = sub_file.stem.split(".")[1]
    if lang_code == "comment":
        track_name = "监督评论"
        lang = "und"
    else:
        if lang_code in ["sc", "SC"]:
            lang = "chi"
            track_name = "简体中文"
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

# 设置默认音频轨道
command.extend(["--default-track", "0:yes"])

# 设置默认字幕轨道
sub_tracks = list(subtitles_dir.glob("PV01.*.ass"))
if len(sub_tracks) == 1:
    command.extend(["--default-track", "0:yes"])
elif len(sub_tracks) > 1:
    for i, sub_file in enumerate(sub_tracks):
        lang_code = sub_file.stem.split(".")[1]
        if lang_code in ["sc", "SC"] and lang_code != "comment":
            command.extend(["--default-track", f"{i}:yes"])
            break

# 执行mkvmerge命令
print(" ".join(command))
subprocess.run(command)

# 重命名音频轨道
info_command = ["mkvinfo", str(output_file)]
info_output = subprocess.run(info_command, capture_output=True, text=True).stdout

audio_tracks = []
for line in info_output.splitlines():
    if "Track type: audio" in line:
        audio_tracks.append({"index": len(audio_tracks)})
    elif "Track number:" in line and audio_tracks:
        audio_tracks[-1]["index"] = int(line.split(":")[1].strip().split(" ")[0])
    elif "Name:" in line and audio_tracks:
        audio_tracks[-1]["name"] = line.split(":")[1].strip()
    elif "Channels:" in line and audio_tracks:
        audio_tracks[-1]["channels"] = int(line.split(":")[1].strip())

for track in audio_tracks:
    if "name" not in track:
        if track.get("channels", 0) == 2:
            track_name = "2ch"
        elif track.get("channels", 0) == 3:
            track_name = "2.1ch"
        elif track.get("channels", 0) == 6:
            track_name = "5.1ch"
        else:
            track_name = f"{track.get('channels', 0)}ch"
        command = [
            "mkvpropedit",
            str(output_file),
            "--edit",
            f"track:a{track['index']}",
            "--set",
            f"name={track_name}",
        ]
        print(" ".join(command))
        subprocess.run(command)

# 重命名AAC音频轨道
aac_tracks = [track for track in audio_tracks if "name" not in track]
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
        f"track:a{track['index']}",
        "--set",
        f"name={track_name}",
    ]
    print(" ".join(command))
    subprocess.run(command)
