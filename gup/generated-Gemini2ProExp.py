import json
import os
import re
import subprocess


def get_track_info(file_path, track_type):
    """
    使用 mkvmerge 获取指定类型轨道的详细信息。

    Args:
        file_path (str): MKV 文件的路径。
        track_type (str): 轨道类型 ('audio', 'subtitles', 'video')。

    Returns:
        list: 包含轨道信息的列表，每个元素是一个字典。
    """
    command = ["mkvmerge", "-i", "-F", "json", file_path]
    result = subprocess.run(command, capture_output=True, text=True)

    # 检查 mkvmerge 是否成功执行
    if result.returncode != 0:
        raise Exception(f"mkvmerge 执行失败: {result.stderr}")

    output_json = result.stdout
    info = json.loads(output_json)

    tracks = []
    for track in info["tracks"]:
        if track["type"] == track_type:
            track_info = {"id": track["id"], "properties": track["properties"]}

            if "track_name" in track["properties"]:
                track_info["name"] = track["properties"]["track_name"]
            if track_type == "audio":
                if "number_of_channels" in track_info["properties"]:
                    track_info["channels"] = track["properties"]["number_of_channels"]
                else:
                    track_info["channels"] = (
                        0  # 对于json中不存在声道信息的情况，例如dts音轨，直接设为0，后续会对其进行修正
                    )
            tracks.append(track_info)

    return tracks


def get_default_audio_track_id(mkv_file, mka_file):
    """获取默认音频轨道的 ID（基于声道数）。"""
    mkv_audio_tracks = get_track_info(mkv_file, "audio")
    mka_audio_tracks = get_track_info(mka_file, "audio") if mka_file else []

    all_audio_tracks = mkv_audio_tracks + mka_audio_tracks
    if not all_audio_tracks:
        return None

    # 解决当json中不存在声道信息时的情况
    for track in all_audio_tracks:
        if (
            track["channels"] == 0
        ):  # 如果是0，说明json中不存在声道数信息, 此时通过mkvinfo重新获取
            command = ["mkvinfo", mkv_file]
            result = subprocess.run(command, capture_output=True, text=True)
            output_text = result.stdout
            # 在 mkvinfo 的输出中找到对应轨道的信息 (这里假设每个轨道的信息是以 "Track number" 开头的)
            track_info_str = re.search(
                rf"Track number: {track['id']}.*?\n(.*?)(?:\nTrack number:|$)",
                output_text,
                re.DOTALL,
            )
            if track_info_str:
                track_info_str = track_info_str.group(1)
                # 在轨道的详细信息里找声道数
                channels_match = re.search(r"Channels: (\d+)", track_info_str)
                if channels_match:
                    track["channels"] = int(channels_match.group(1))  # 更新声道数

    max_channels = max(track["channels"] for track in all_audio_tracks)
    for track in all_audio_tracks:
        if track["channels"] == max_channels:
            return track["id"], (mka_file is not None and track in mka_audio_tracks)

    return None, None


def generate_mkvmerge_command(
    input_mkv, input_mka, subtitle_files, font_files, output_mkv
):
    """生成 mkvmerge 命令行参数。"""
    command = ["mkvmerge", "-o", output_mkv]

    # 添加 MKV 文件
    command.extend(["-d", "0", input_mkv])

    # 复制原有视频轨道
    video_tracks = get_track_info(input_mkv, "video")
    for track in video_tracks:
        command.extend(["-D", "--no-chapters", input_mkv, "-d", str(track["id"])])

    # 添加音轨并设置默认音轨
    default_audio_track_id, is_mka = get_default_audio_track_id(input_mkv, input_mka)

    # 处理mkv中的音轨
    mkv_audio_tracks = get_track_info(input_mkv, "audio")
    for track in mkv_audio_tracks:
        command.extend(["-a", str(track["id"])])
        if track["id"] == default_audio_track_id and not is_mka:
            command.extend(["--default-track", f"{track['id']}:yes"])
        else:
            command.extend(["--default-track", f"{track['id']}:no"])
        # 如果音轨有名称则保留，否则按照规则命名
        if "name" not in track:
            if track["properties"]["codec_id"] == "A_FLAC":
                if track["channels"] == 2:
                    command.extend(["--track-name", f"{track['id']}:2ch"])
                elif track["channels"] == 3:
                    command.extend(["--track-name", f"{track['id']}:2.1ch"])
                elif track["channels"] == 6:
                    command.extend(["--track-name", f"{track['id']}:5.1ch"])
            elif track["properties"]["codec_id"] == "A_AAC":
                # aac轨道名称不在这里命名，在后续操作命名
                pass

    # 添加 MKA 文件（如果存在）
    if input_mka:
        command.append(input_mka)
        if default_audio_track_id is not None and is_mka:
            command.extend(["--default-track", "0:yes"])  # MKA 中的第一轨通常是 0
        else:
            command.extend(["--default-track", "0:no"])

    # 添加字幕文件
    subtitle_tracks_count = 0
    default_subtitle_set = False

    mkv_subtitle_tracks = get_track_info(input_mkv, "subtitles")
    for track in mkv_subtitle_tracks:
        command.extend(["-s", str(track["id"]), input_mkv])
        subtitle_tracks_count += 1
        if "name" not in track:
            # 如果有名字则保留，没有名字则按照规则命名
            if "language" in track["properties"]:
                if track["properties"]["language"] == "jpn":
                    command.extend(["--track-name", f"{track['id']}:日文"])
                elif track["properties"]["language"] == "zho":
                    if "language_ietf" in track["properties"] and (
                        track["properties"]["language_ietf"] == "zh-CN"
                        or track["properties"]["language_ietf"] == "zh-Hans"
                    ):
                        command.extend(["--track-name", f"{track['id']}:简体中文"])
                    elif "language_ietf" in track["properties"] and (
                        track["properties"]["language_ietf"] == "zh-TW"
                        or track["properties"]["language_ietf"] == "zh-Hant"
                    ):
                        command.extend(["--track-name", f"{track['id']}:繁体中文"])
                    else:
                        command.extend(["--track-name", f"{track['id']}:未知"])
                else:
                    command.extend(["--track-name", f"{track['id']}:未知"])
            else:
                command.extend(["--track-name", f"{track['id']}:未知"])

    for subtitle in subtitle_files:
        subtitle_tracks_count += 1
        basename = os.path.basename(subtitle)
        lang_code = basename.split(".")[-2].lower()

        language_map = {
            "ja": ("jpn", "日文"),
            "sc": ("zho", "简体中文"),
            "tc": ("zho", "繁体中文"),
            "zh": ("zho", "简体中文"),
        }

        lang_ietf_map = {"sc": "zh-CN", "tc": "zh-TW"}

        if lang_code == "comment":
            command.extend(
                [
                    "--language",
                    f"{subtitle_tracks_count - 1}:zho",
                    "--track-name",
                    f"{subtitle_tracks_count - 1}:监督评论",
                    subtitle,
                ]
            )
        elif lang_code in language_map:
            lang, name = language_map[lang_code]
            # 使用 --language 替代 --language-ietf
            command.extend(
                [
                    "--language",
                    f"{subtitle_tracks_count - 1}:{lang}",
                    "--track-name",
                    f"{subtitle_tracks_count - 1}:{name}",
                    subtitle,
                ]
            )

            if lang == "zho" and name == "简体中文" and not default_subtitle_set:
                command.extend(["--default-track", f"{subtitle_tracks_count - 1}:yes"])
                default_subtitle_set = True
        else:
            # 对于没有语言代码的，默认为简体中文
            command.extend(
                [
                    "--language",
                    f"{subtitle_tracks_count - 1}:zho",
                    "--track-name",
                    f"{subtitle_tracks_count - 1}:简体中文",
                    subtitle,
                ]
            )
            if not default_subtitle_set:
                command.extend(["--default-track", f"{subtitle_tracks_count - 1}:yes"])
                default_subtitle_set = True

    # 只有一个字幕轨道，则设为默认
    if subtitle_tracks_count == 1 and not default_subtitle_set:
        command.extend(["--default-track", f"{subtitle_tracks_count - 1}:yes"])
    # 添加字体文件
    for font in font_files:
        command.extend(
            [
                "--attachment-mime-type",
                "application/x-truetype-font",
                "--attach-file",
                font,
            ]
        )

    return command


def rename_aac_tracks(mkv_file):
    """重命名 AAC 音轨。"""
    audio_tracks = get_track_info(mkv_file, "audio")
    aac_tracks = [
        track
        for track in audio_tracks
        if track["properties"]["codec_id"] == "A_AAC" and "name" not in track
    ]

    # 如果没有需要命名的aac音轨，则直接返回
    if not aac_tracks:
        return

    names = ["声优评论", "监督评论", "军事评论"]

    # 构建一个临时的 mkvmerge 命令来重命名轨道
    # 添加 -y 参数，如果输出文件存在则覆盖
    temp_command = ["mkvmerge", "-y", "-o", "temp.mkv", mkv_file]

    for i, track in enumerate(aac_tracks):
        if i < len(names):
            temp_command.extend(["--track-name", f"{track['id']}:{names[i]}"])
    # 如果音轨数量大于名称数量，剩余的音轨使用默认名称或其他逻辑

    # 执行临时命令来应用更改
    subprocess.run(temp_command)
    # 替换原始文件
    os.replace("temp.mkv", mkv_file)


def main():
    input_mkv = "PV01.mkv"
    input_mka = "PV01.mka" if os.path.exists("PV01.mka") else None
    output_mkv = os.path.join("dist", "PV01_merged.mkv")
    subtitle_dir = os.path.join("dist", "subsetted")

    subtitle_files = []
    for f in os.listdir(subtitle_dir):
        if f.startswith("PV01") and f.lower().endswith(".ass"):
            subtitle_files.append(os.path.join(subtitle_dir, f))

    font_files = [
        os.path.join(subtitle_dir, f)
        for f in os.listdir(subtitle_dir)
        if f.lower().endswith((".otf", ".ttf", ".ttc"))
    ]

    # 生成 mkvmerge 命令并执行
    command = generate_mkvmerge_command(
        input_mkv, input_mka, subtitle_files, font_files, output_mkv
    )
    print("执行的命令:", " ".join(command))  # 调试：打印生成的命令
    result = subprocess.run(
        command, capture_output=True, text=True
    )  # 使用 capture_output=True 捕获输出
    if result.returncode != 0:
        print(f"mkvmerge 错误输出: {result.stderr}")  # 打印错误
    else:
        print(f"mkvmerge 标准输出: {result.stdout}")  # 打印输出

    # 重命名 AAC 音轨
    rename_aac_tracks(output_mkv)


if __name__ == "__main__":
    main()
