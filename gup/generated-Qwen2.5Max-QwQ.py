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

# 添加视频文件及其参数
command.append(video_file)
# 添加视频内音频轨道参数（如果有）
video_audio_tracks = get_audio_tracks(video_file)
for track in video_audio_tracks:
    command.append(
        f"--default-track-flag {track['track_id']}:{'yes' if track['channels'] >= 2 else 'no'}"
    )

# 添加外部音频文件及其参数（如果存在）
if os.path.exists(audio_file):
    command.append(audio_file)
    external_audio_tracks = get_audio_tracks(audio_file)
    for track in external_audio_tracks:
        command.append(
            f"--default-track-flag {track['track_id']}:{'yes' if track['channels'] >= 2 else 'no'}"
        )

# 添加外部字幕文件
command.append("--no-subtitles")  # 禁用源文件字幕

# 处理外部字幕文件
for f in os.listdir(subtitle_dir):
    if f.startswith("PV01.") and f.endswith(".ass"):
        # 解析语言代码
        base = os.path.splitext(f)[0]
        code = base.split(".")[1].lower() if "." in base else ""
        lang = "und"
        name = "简体中文"
        if code == "sc":
            lang = "zho"
            name = "简体中文"
        elif code == "tc":
            lang = "zho"
            name = "繁体中文"
        elif code == "comment":
            lang = "und"
            name = "监督评论"

        # 添加字幕参数（每个文件独立）
        command.extend(
            [
                "--language",
                "0:{}".format(lang),
                "--track-name",
                "0:{}".format(name),
                "--default-track-flag",
                "0:{}".format("yes" if code == "sc" else "no"),
                os.path.join(subtitle_dir, f),
            ]
        )

# 添加字体附件
for f in os.listdir(subtitle_dir):
    if f.lower().endswith((".otf", ".ttf", ".ttc")):
        command.append(f"--attach-file {os.path.join(subtitle_dir, f)}")

# 执行命令
print(" ".join(command))
subprocess.run(" ".join(command), shell=True)
