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


def get_subtitle_tracks(file):
    cmd = ["mkvmerge", "-J", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    tracks = []
    for track in info["tracks"]:
        if track["type"] == "subtitles":
            tracks.append(
                {
                    "file": file,
                    "track_id": track["id"],
                    "language": track["properties"].get("language", "und"),
                    "name": track["properties"].get("track_name", ""),
                    "is_default": track["properties"].get("default_track", False),
                }
            )
    return tracks


video_file = "PV01.mkv"
audio_file = "PV01.mka"
subtitle_dir = "dist/subsetted"
output_file = "dist/PV01_new.mkv"

subtitle_files = []
for f in os.listdir(subtitle_dir):
    if f.startswith("PV01.") and f.endswith(".ass"):
        if not any(f.lower().endswith(ext) for ext in [".otf", ".ttf", ".ttc"]):
            subtitle_files.append(os.path.join(subtitle_dir, f))

new_subtitles = []
for f in subtitle_files:
    base = os.path.splitext(os.path.basename(f))[0]
    # 修正文件名解析逻辑：直接取第二个部分作为语言代码
    code = base.split(".")[1].lower() if "." in base else ""
    lang = "und"
    name = "简体中文"
    if code == "comment":
        lang = "und"
        name = "监督评论"
    elif code in ["ja"]:
        lang = "jpn"
        name = "日语"
    elif code in ["sc"]:
        lang = "zho"
        name = "简体中文"
    elif code in ["tc"]:
        lang = "zho"
        name = "繁体中文"
    new_subtitles.append(
        {
            "file": f,
            "language": lang,
            "name": name,
            "code": code,  # 保留原始代码用于调试
        }
    )

video_subtitles = get_subtitle_tracks(video_file)
all_subtitles = video_subtitles.copy()
for sub in new_subtitles:
    all_subtitles.append(
        {
            "file": sub["file"],
            "language": sub["language"],
            "name": sub["name"],
            "code": sub["code"],
        }
    )

default_subtitle = None
if len(all_subtitles) == 1:
    default_subtitle = all_subtitles[0]
else:
    sc_non_comment = [
        s
        for s in all_subtitles
        if s.get("language") == "zho"
        and s.get("code") in ["sc"]  # 确保是简体中文非评论
        and not s.get("name", "") == "监督评论"
    ]
    if sc_non_comment:
        default_subtitle = sc_non_comment[0]
    else:
        non_comment = [s for s in all_subtitles if not s.get("name", "") == "监督评论"]
        if non_comment:
            default_subtitle = non_comment[0]

audio_tracks = get_audio_tracks(video_file)
if os.path.exists(audio_file):
    audio_tracks += get_audio_tracks(audio_file)

default_audio = max(audio_tracks, key=lambda x: x["channels"]) if audio_tracks else None

command = ["mkvmerge", "-o", output_file]

# 添加视频文件及其音频参数
command.append(video_file)
for track in audio_tracks:
    if track["file"] == video_file:
        command.append(
            f"--default-track-flag {track['track_id']}:{'yes' if track == default_audio else 'no'}"
        )
        if track["name"]:
            command.append(f"--track-name {track['track_id']}:{track['name']}")

# 添加外部音频文件
if os.path.exists(audio_file):
    command.append(audio_file)
    for track in audio_tracks:
        if track["file"] == audio_file:
            command.append(
                f"--default-track-flag {track['track_id']}:{'yes' if track == default_audio else 'no'}"
            )
            if track["name"]:
                command.append(f"--track-name {track['track_id']}:{track['name']}")

# 处理字幕
command.append("--no-subtitles")

for sub in all_subtitles:
    if "file" in sub and sub["file"] != video_file:
        # 处理外部字幕文件
        lang = sub["language"]
        name = sub["name"]
        default = "yes" if sub == default_subtitle else "no"
        command.extend(
            [
                "--language",
                f"0:{lang}",
                "--track-name",
                f"0:{name}",
                "--default-track-flag",
                f"0:{default}",
                sub["file"],
            ]
        )

# 添加字体附件
fonts = [
    os.path.join(subtitle_dir, f)
    for f in os.listdir(subtitle_dir)
    if f.lower().endswith((".otf", ".ttf", ".ttc"))
]
for font in fonts:
    command.append(f"--attach-file {font}")

# 执行命令
print(" ".join(command))
subprocess.run(" ".join(command), shell=True)
