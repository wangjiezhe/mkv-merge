import json
import os
import re
import subprocess
import sys
from pathlib import Path


def get_track_info(file_path):
    """获取mkv/mka文件的轨道信息"""
    cmd = ["mkvmerge", "-J", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting track info: {result.stderr}")
        return None
    return json.loads(result.stdout)


def get_channel_count(track):
    """获取音频轨道的声道数"""
    properties = track.get("properties", {})
    if "audio_channels" in properties:
        return properties["audio_channels"]
    return 0


def get_language_name(lang_code):
    """返回语言代码对应的语言名称"""
    language_map = {
        "ja": "日语",
        "sc": "简体中文",
        "tc": "繁体中文",
        "en": "英语",
        "zh": "中文",
        "zh-hans": "简体中文",
        "zh-cn": "简体中文",
        "zh-hant": "繁体中文",
        "zh-tw": "繁体中文",
        "zh-hk": "繁体中文",
    }
    return language_map.get(lang_code.lower(), lang_code)


def process_files():
    # 确保输出目录存在
    os.makedirs("dist", exist_ok=True)

    # 检查视频文件是否存在
    if not os.path.exists("PV01.mkv"):
        print("Error: PV01.mkv not found")
        return

    # 构建mkvmerge命令
    cmd = ["mkvmerge", "-o", "dist/PV01.mkv"]

    # 处理主MKV文件
    video_info = get_track_info("PV01.mkv")
    if video_info is None:
        return

    # 保存所有音频轨道信息，用于后续确定默认轨道
    all_audio_tracks = []
    default_audio_track_id = None
    max_channel_count = 0

    # 获取MKV中的音频轨道信息
    for track in video_info.get("tracks", []):
        if track["type"] == "audio":
            channel_count = get_channel_count(track)
            all_audio_tracks.append(
                {
                    "file": "PV01.mkv",
                    "id": track["id"],
                    "channel_count": channel_count,
                    "codec": track.get("codec", ""),
                    "name": track.get("properties", {}).get("track_name", ""),
                }
            )
            if channel_count > max_channel_count:
                max_channel_count = channel_count
                default_audio_track_id = track["id"]

    # 添加视频文件
    cmd.extend(["PV01.mkv"])

    # 处理MKA文件(如果存在)
    if os.path.exists("PV01.mka"):
        audio_info = get_track_info("PV01.mka")
        if audio_info is not None:
            for track in audio_info.get("tracks", []):
                if track["type"] == "audio":
                    channel_count = get_channel_count(track)
                    all_audio_tracks.append(
                        {
                            "file": "PV01.mka",
                            "id": track["id"],
                            "channel_count": channel_count,
                            "codec": track.get("codec", ""),
                            "name": track.get("properties", {}).get("track_name", ""),
                        }
                    )
                    if channel_count > max_channel_count:
                        max_channel_count = channel_count
                        default_audio_track_id = (
                            None  # 如果MKA中有更多声道，将重置默认ID
                        )

            # 添加MKA文件
            cmd.extend(
                ["--append-to", f"0:{len(video_info.get('tracks', []))}", "PV01.mka"]
            )

    # 收集字幕文件
    subtitle_files = []
    default_subtitle_id = None

    # 检查dist/subsetted目录是否存在
    subsetted_dir = Path("dist/subsetted")
    if subsetted_dir.exists() and subsetted_dir.is_dir():
        # 查找所有字幕文件
        for file in subsetted_dir.glob("PV01.*.ass"):
            file_name = file.name
            match = re.search(r"PV01\.([^.]+)\.ass", file_name)
            if match:
                lang_code = match.group(1).lower()
                is_comment = lang_code == "comment"

                subtitle_info = {
                    "path": str(file),
                    "lang_code": "chi"
                    if is_comment
                    else lang_code,  # 使用ISO 639-2语言代码
                    "name": "监督评论" if is_comment else get_language_name(lang_code),
                }

                # 检查是否为简体中文
                is_sc = lang_code in ["sc", "zh", "zh-hans", "zh-cn"]

                if is_sc and not is_comment and default_subtitle_id is None:
                    default_subtitle_id = len(subtitle_files)

                subtitle_files.append(subtitle_info)

    # 如果只有一个字幕文件，设置为默认
    if len(subtitle_files) == 1:
        default_subtitle_id = 0

    # 添加字幕文件
    for idx, subtitle in enumerate(subtitle_files):
        lang_param = f"--language=0:{subtitle['lang_code']}"
        name_param = f"--track-name=0:{subtitle['name']}"
        default_param = (
            "--default-track=0:yes"
            if idx == default_subtitle_id
            else "--default-track=0:no"
        )
        cmd.extend([lang_param, name_param, default_param, subtitle["path"]])

    # 收集字体文件
    font_files = []
    if subsetted_dir.exists() and subsetted_dir.is_dir():
        # 查找所有字体文件
        font_extensions = [".otf", ".ttf", ".ttc", ".OTF", ".TTF", ".TTC"]
        for ext in font_extensions:
            for file in subsetted_dir.glob(f"*{ext}"):
                font_files.append(str(file))

    # 添加字体文件附件
    for font_file in font_files:
        font_name = os.path.basename(font_file)
        cmd.extend(
            [
                "--attachment-name",
                font_name,
                "--attachment-mime-type",
                "application/x-truetype-font",
                "--attach-file",
                font_file,
            ]
        )

    # 设置音频轨道名称和默认轨道
    aac_names = ["声优评论", "监督评论", "军事评论"]
    aac_count = 0

    for idx, track in enumerate(all_audio_tracks):
        track_id = track["id"]
        file_index = cmd.index(track["file"])

        # 设置默认轨道
        is_default = False
        if track["file"] == "PV01.mkv" and track_id == default_audio_track_id:
            is_default = True
        elif (
            track["file"] == "PV01.mka"
            and default_audio_track_id is None
            and track["channel_count"] == max_channel_count
        ):
            is_default = True
            default_audio_track_id = track_id

        default_param = (
            f"--default-track={track_id}:yes"
            if is_default
            else f"--default-track={track_id}:no"
        )
        cmd.insert(file_index, default_param)

        # 设置轨道名称（如果原来没有名称）
        if not track["name"]:
            if track["codec"] == "FLAC":
                # 根据声道数设置FLAC轨道名称
                channels = track["channel_count"]
                if channels == 6:
                    name = "5.1ch"
                elif channels == 3:
                    name = "2.1ch"
                elif channels == 2:
                    name = "2ch"
                else:
                    name = f"{channels}ch"

                name_param = f"--track-name={track_id}:{name}"
                cmd.insert(file_index, name_param)

            elif track["codec"] == "AAC":
                # 为AAC轨道设置名称
                if aac_count < len(aac_names):
                    name_param = f"--track-name={track_id}:{aac_names[aac_count]}"
                    cmd.insert(file_index, name_param)
                    aac_count += 1

    # 执行命令
    print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("Successfully created dist/PV01.mkv")
    else:
        print(f"Error creating MKV: {result.stderr}")


if __name__ == "__main__":
    process_files()
