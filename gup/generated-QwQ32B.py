import glob
import os
import subprocess


def main():
    # 输入文件路径
    video_file = "PV01.mkv"
    mka_file = "PV01.mka" if os.path.exists("PV01.mka") else None
    subsetted_dir = "dist/subsetted"
    output_file = "dist/PV01_merged.mkv"

    # 处理字幕
    subtitles = []
    subtitle_files = glob.glob(os.path.join(subsetted_dir, f"PV01.*.ass"))
    for sub_file in subtitle_files:
        base = os.path.basename(sub_file)
        parts = base.split(".")
        lang_part = parts[1].lower()
        if lang_part == "comment":
            track_name = "监督评论"
            language = "ja"
        else:
            if lang_part in ["sc", "tc"]:
                language = "zh" if lang_part == "sc" else "zh-TW"
                track_name = "简体中文" if lang_part == "sc" else "繁体中文"
            else:
                language = lang_part
                track_name = lang_part.title()
        subtitles.append(
            {
                "file": sub_file,
                "track_name": track_name,
                "language": language,
                "is_comment": lang_part == "comment",
            }
        )

    # 确定默认字幕轨道
    default_sub = None
    if len(subtitles) == 1:
        default_sub = subtitles[0]
    else:
        sc_subs = [
            s
            for s in subtitles
            if s["language"].startswith("zh") and not s["is_comment"]
        ]
        if sc_subs:
            default_sub = sc_subs[0]
        else:
            non_comment = [s for s in subtitles if not s["is_comment"]]
            if non_comment:
                default_sub = non_comment[0]
            else:
                default_sub = subtitles[0]

    # 处理字体文件
    fonts = []
    for ext in ("*.otf", "*.ttf", "*.ttc", "*.OTF", "*.TTF", "*.TTC"):
        fonts.extend(glob.glob(os.path.join(subsetted_dir, ext)))

    # 处理音频轨道
    def get_audio_tracks(file_path):
        cmd = ["mkvmerge", "-i", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.split("\n")
        tracks = []
        for line in lines:
            if "Track ID" in line and "audio" in line:
                parts = line.split()
                track_id = int(parts[2].split(":")[0])
                codec = parts[3]
                channels = 0
                for p in parts:
                    if "channel" in p:
                        channels = int(p.split("(")[0].strip())
                        break
                name_part = [p for p in parts if p.startswith("name:")]
                name = name_part[0].split(":", 1)[1].strip() if name_part else ""
                tracks.append(
                    {
                        "file": file_path,
                        "track_id": track_id,
                        "codec": codec,
                        "channels": channels,
                        "name": name,
                    }
                )
        return tracks

    video_audio = get_audio_tracks(video_file)
    mka_audio = get_audio_tracks(mka_file) if mka_file else []
    all_audio = video_audio + mka_audio

    # 找到声道最多的音频轨道
    default_audio = None
    if all_audio:
        max_channels = max(t["channels"] for t in all_audio)
        default_audio_candidates = [
            t for t in all_audio if t["channels"] == max_channels
        ]
        default_audio = default_audio_candidates[0]

    # 构建mkvmerge命令
    cmd = ["mkvmerge", "-o", output_file]

    # 添加输入文件
    cmd.append(video_file)
    if mka_file:
        cmd.append(mka_file)
    # 添加字幕轨道
    for sub in subtitles:
        cmd.append(sub["file"])

    # 添加字体文件作为附加文件
    for font in fonts:
        cmd.extend(["--attach-file", font])
        cmd.extend(["--attachment-mime-type", "application/x-truetype-font"])

    # 处理轨道参数
    track_params = []

    # 字幕轨道参数
    audio_count = len(all_audio)
    subtitle_count = len(subtitles)
    for i, sub in enumerate(subtitles):
        track_num = audio_count + 1 + i
        # 移除引号并修正轨道ID计算
        track_params.append(f"--track-name {track_num}:{sub['track_name']}")
        track_params.append(f"--language {track_num}:{sub['language']}")
        if sub == default_sub:
            track_params.append(f"--default-track {track_num}:yes")
        else:
            track_params.append(f"--default-track {track_num}:no")

    # 音频轨道默认设置
    if default_audio:
        if default_audio["file"] == video_file:
            merged_id = default_audio["track_id"]
        else:
            merged_id = len(video_audio) + default_audio["track_id"]
        track_params.append(f"--default-track {merged_id}:yes")

    # 处理FLAC轨道重命名
    for track in all_audio:
        if track["codec"].lower() == "flac" and not track["name"]:
            channels = track["channels"]
            new_name = f"{channels if channels != 6 else '5.1'}ch"
            if track["file"] == video_file:
                merged_id = track["track_id"]
            else:
                merged_id = len(video_audio) + track["track_id"]
            track_params.append(f"--track-name {merged_id}:{new_name}")

    # 处理AAC轨道重命名
    aac_tracks = [t for t in all_audio if t["codec"].lower() == "aac"]
    for idx, track in enumerate(aac_tracks):
        if not track["name"]:
            names = ["声优评论", "监督评论", "军事评论"]
            new_name = names[idx] if idx < len(names) else ""
            if new_name:
                if track["file"] == video_file:
                    merged_id = track["track_id"]
                else:
                    merged_id = len(video_audio) + track["track_id"]
                track_params.append(f"--track-name {merged_id}:{new_name}")

    # 添加所有参数到命令
    cmd.extend(track_params)
    print(cmd)

    # 执行命令
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
