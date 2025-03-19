import json
import os
import subprocess


def get_audio_tracks(file, file_index):
    cmd = ["mkvmerge", "-J", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    tracks = []
    for idx, track in enumerate(info["tracks"]):  # 使用枚举获取顺序索引
        if track["type"] == "audio":
            codec = track["codec"]
            channels = track["properties"].get("audio_channels", 0)
            track_id = idx  # 使用顺序索引而非原始 ID
            name = track["properties"].get("track_name", "")
            tracks.append(
                {
                    "file_index": file_index,
                    "file": file,
                    "track_id": track_id,
                    "codec": codec,
                    "channels": channels,
                    "name": name,
                }
            )
    return tracks


def get_subtitle_tracks(file, file_index):
    cmd = ["mkvmerge", "-J", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    tracks = []
    for idx, track in enumerate(info["tracks"]):  # 使用枚举获取顺序索引
        if track["type"] == "subtitles":
            track_id = idx  # 使用顺序索引
            tracks.append(
                {
                    "file_index": file_index,
                    "track_id": track_id,
                    "language": track["properties"].get("language", "und"),
                    "name": track["properties"].get("track_name", ""),
                    "is_default": track["properties"].get("default_track", False),
                    "is_forced": track["properties"].get("forced_track", False),
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
        if any(f.lower().endswith(ext) for ext in [".otf", ".ttf", ".ttc"]):
            continue
        subtitle_files.append(os.path.join(subtitle_dir, f))

new_subtitles = []
for f in subtitle_files:
    base = os.path.splitext(os.path.basename(f))[0]
    parts = base.split(".")[1:-1] if "." in base else []
    code = parts[0].lower() if parts else ""
    lang = "und"
    name = "简体中文"
    is_comment = False
    if code == "comment":
        lang = "und"
        name = "监督评论"
        is_comment = True
    elif code in ["ja"]:
        lang = "jpn"
        name = "日语"
    elif code in ["sc", "tc"]:
        lang = "zho"
        name = "简体中文" if code == "sc" else "繁体中文"
    new_subtitles.append(
        {"file": f, "language": lang, "name": name, "is_comment": is_comment}
    )

video_subtitles = get_subtitle_tracks(video_file, 0)
all_subtitles = video_subtitles.copy()
for sub in new_subtitles:
    all_subtitles.append(
        {
            "file": sub["file"],
            "language": sub["language"],
            "name": sub["name"],
            "is_comment": sub["is_comment"],
        }
    )

default_subtitle = None
if len(all_subtitles) == 1:
    default_subtitle = all_subtitles[0]
else:
    sc_non_comment = [
        s
        for s in all_subtitles
        if s.get("language") == "zho" and not s.get("is_comment", False)
    ]
    if sc_non_comment:
        default_subtitle = sc_non_comment[0]
    else:
        non_comment = [s for s in all_subtitles if not s.get("is_comment", False)]
        if non_comment:
            default_subtitle = non_comment[0]

audio_tracks = []
file_index = 0
audio_tracks += get_audio_tracks(video_file, file_index)
if os.path.exists(audio_file):
    file_index += 1
    audio_tracks += get_audio_tracks(audio_file, file_index)

default_audio = max(audio_tracks, key=lambda x: x["channels"]) if audio_tracks else None

audio_args = []
aac_index = 0
for track in audio_tracks:
    is_default = track == default_audio
    # 使用文件索引和顺序索引组合
    default_flag = f"--default-track-flag {track['file_index']}:{track['track_id']}:{'yes' if is_default else 'no'}"
    name = track["name"]
    if not name:
        if track["codec"] == "FLAC":
            name = f"FLAC {track['channels']}ch"
        elif track["codec"] == "AAC":
            if aac_index < 3:
                name = ["声优评论", "监督评论", "军事评论"][aac_index]
                aac_index += 1
            else:
                name = f"AAC Track {aac_index + 1}"
    name_arg = (
        f"--track-name {track['file_index']}:{track['track_id']}:{name}" if name else ""
    )
    audio_args.append(f"{default_flag} {name_arg}")

subtitle_args = []
for sub in all_subtitles:
    if "file" in sub:
        lang = sub["language"]
        name = sub["name"]
        # 新增字幕文件使用文件索引 0（自身）
        default_flag = (
            f"--default-track-flag 0:{'yes' if sub == default_subtitle else 'no'}"
        )
        args = (
            f'--language 0:{lang} --track-name 0:"{name}" {default_flag} {sub["file"]}'
        )
        subtitle_args.append(args)
    else:
        # 视频内字幕使用原文件索引和顺序索引
        default_flag = f"--default-track-flag {sub['file_index']}:{sub['track_id']}:{'yes' if sub == default_subtitle else 'no'}"
        subtitle_args.append(default_flag)

fonts = []
for f in os.listdir(subtitle_dir):
    if f.lower().endswith((".otf", ".ttf", ".ttc")):
        fonts.append(os.path.join(subtitle_dir, f))
attach_args = [f"--attach-file {f}" for f in fonts]

# 重新组织命令参数，确保每个文件的参数紧跟文件名
command = ["mkvmerge", "-o", output_file]

# 添加视频文件及其音频参数
command.append(video_file)
video_audio_args = []
for track in audio_tracks:
    if track["file_index"] == 0:  # 属于视频文件的音频轨道
        video_audio_args.extend(
            [
                f"--default-track-flag 0:{track['track_id']}:{'yes' if track == default_audio else 'no'}",
                f"--track-name 0:{track['track_id']}:{track['name']}"
                if track["name"]
                else "",
            ]
        )
command.extend(video_audio_args)

# 添加外部音频文件及其参数
if os.path.exists(audio_file):
    command.append(audio_file)
    external_audio_args = []
    for track in audio_tracks:
        if track["file_index"] == 1:  # 属于外部音频文件的轨道
            external_audio_args.extend(
                [
                    f"--default-track-flag 1:{track['track_id']}:{'yes' if track == default_audio else 'no'}",
                    f"--track-name 1:{track['track_id']}:{track['name']}"
                    if track["name"]
                    else "",
                ]
            )
    command.extend(external_audio_args)

# 添加字幕参数
command.extend(["--no-subtitles", *subtitle_args, *attach_args])

print(" ".join(command))
subprocess.run(" ".join(command), shell=True)
