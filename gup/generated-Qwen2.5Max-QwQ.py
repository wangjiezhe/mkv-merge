import json
import os
import subprocess


def get_audio_tracks(file):
    cmd = ["mkvmerge", "-J", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    tracks = []
    for track in info["tracks"]:
        if track["type"] == "audio":
            codec = track["codec"]
            channels = track["properties"].get("audio_channels", 0)
            track_id = track["id"]
            name = track["properties"].get("track_name", "")
            tracks.append(
                {
                    "file": file,
                    "track_id": track_id,
                    "codec": codec,
                    "channels": channels,
                    "name": name,
                }
            )
    return tracks


video_file = "PV01.mkv"
audio_file = "PV01.mka"
subtitle_dir = "dist/subsetted"
output_file = "dist/PV01_new.mkv"

# 构建命令
command = ["mkvmerge", "-o", output_file]

# 1. 添加视频文件及其参数
video_audio_tracks = get_audio_tracks(video_file)
for track in video_audio_tracks:
    # 视频文件的音频参数紧跟在视频文件名之后
    command.append(
        f"--default-track-flag {track['track_id']}:{'yes' if track['channels'] >= 2 else 'no'}"
    )

command.append(video_file)

# 2. 添加外部音频文件及其参数（如果存在）
if os.path.exists(audio_file):
    external_audio_tracks = get_audio_tracks(audio_file)
    for track in external_audio_tracks:
        # 外部音频参数紧跟在音频文件名之后
        command.append(
            f"--default-track-flag {track['track_id']}:{'yes' if track['channels'] >= 2 else 'no'}"
        )

    command.append(audio_file)  # 先添加文件名

# 3. 添加外部字幕文件（每个文件独立参数组）
# command.append("--no-subtitles")  # 禁用源文件字幕

for f in os.listdir(subtitle_dir):
    if f.startswith("PV01.") and f.endswith(".ass"):
        # 解析语言代码
        base = os.path.splitext(f)[0]
        code = base.split(".")[1].lower() if "." in base else ""
        lang = "und"
        name = "简体中文"
        default = "no"

        if code == "sc":
            lang = "zho"
            name = "简体中文"
            default = "yes"
        elif code == "tc":
            lang = "zho"
            name = "繁体中文"
        elif code == "comment":
            lang = "und"
            name = "监督评论"

        # 添加字幕参数（每个文件独立，参数紧跟文件名）
        command.extend(
            [
                "--language",
                "0:{}".format(lang),
                "--track-name",
                "0:{}".format(name),
                "--default-track-flag",
                "0:{}".format(default),
                os.path.join(subtitle_dir, f),
            ]
        )

# 4. 添加字体附件
for f in os.listdir(subtitle_dir):
    if f.lower().endswith((".otf", ".ttf", ".ttc")):
        command.append(f"--attach-file {os.path.join(subtitle_dir, f)}")

# 执行命令
print(" ".join(command))
subprocess.run(" ".join(command), shell=True)
