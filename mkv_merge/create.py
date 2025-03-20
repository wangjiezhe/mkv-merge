import json
import os
import shutil
import subprocess
import tempfile
from itertools import chain
from pathlib import Path
from typing import Tuple

from mkv_merge.logging import lcb
from mkv_merge.mkvlib import sdk


def get_track_info(file_path: str):
    result = subprocess.run(
        ["mkvmerge", "-J", file_path], capture_output=True, text=True, encoding="utf-8"
    )
    return json.loads(result.stdout)


def get_channel_count(track: dict):
    channels = track.get("properties", {}).get("audio_channels", 2)
    return channels


def process_subtitle_language(filename: str) -> Tuple[str, str]:
    parts = filename.split(".")
    if len(parts) < 3:
        return "zh-CN", "简体中文"

    lang_part = parts[-2].lower()
    if lang_part == "comment":
        return "zh-CN", "监督评论"
    elif lang_part == "ja":
        return "ja", "日本語"
    elif lang_part in ["zh", "chi"]:
        return "zh-CN", "简体中文"
    elif lang_part in ["sc", "chs"]:
        return "zh-CN", "简体中文"
    elif lang_part in ["tc", "cht"]:
        return "zh-TW", "繁體中文"
    else:
        return "und", "未知语言"


def create_mkv(
    video_file: str, output_dir: str, font_dir: str, save_temp_fonts: bool = False
):
    audio_file = Path(video_file).with_suffix(".mka").as_posix()
    output_file = os.path.join(output_dir, Path(video_file).name)
    subsetted_dir = tempfile.mkdtemp(prefix="subsetted-")

    # Base command
    cmd = ["mkvmerge", "-o", output_file]

    # Handle video file
    get_track_info(video_file)
    cmd.extend([video_file])

    # Handle audio file if exists
    audio_tracks = []
    if os.path.exists(audio_file):
        audio_info = get_track_info(audio_file)
        audio_tracks.extend(audio_info["tracks"])
        cmd.extend([audio_file])

    # Handle subtitles
    video_stem = Path(video_file).stem
    video_dir = Path(video_file).parent
    subtitle_files = list(
        chain(
            video_dir.glob(f"{video_stem}.ass"),
            video_dir.glob(f"{video_stem}.*.ass"),
        )
    )

    if subtitle_files:
        # Sort subtitle files based on language preference
        language_order = ["日本語", "简体中文", "繁體中文", "监督评论"]
        subtitle_files.sort(
            key=lambda f: language_order.index(process_subtitle_language(f.name)[1])
            if process_subtitle_language(f.name)[1] in language_order
            else len(language_order)
        )

        # 子集化字体
        is_success = sdk.assFontSubset(
            [ass.as_posix() for ass in subtitle_files],
            font_dir,
            subsetted_dir,
            False,
            lcb,
        )
        if not is_success:
            raise RuntimeError("Font subset failed.")

        for sub_file in subtitle_files:
            lang_code, track_name = process_subtitle_language(sub_file.name)
            cmd.extend(["--language", f"0:{lang_code}", "--sub-charset", "0:UTF-8"])
            cmd.extend(["--track-name", f"0:{track_name}"])
            cmd.append(sub_file.as_posix())

        # Handle fonts
        font_files = [
            f
            for f in os.listdir(subsetted_dir)
            if f.lower().endswith((".otf", ".ttf", ".ttc"))
        ]
        if font_files:
            cmd.append("--attachment-mime-type")
            cmd.append("application/x-truetype-font")
            for font in font_files:
                cmd.extend(["--attach-file", os.path.join(subsetted_dir, font)])

    # Execute mkvmerge
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    # Post-processing with mkvpropedit
    output_info = get_track_info(output_file)
    prop_cmd = ["mkvpropedit", output_file]

    # Handle subtitle defaults
    subtitle_tracks = [t for t in output_info["tracks"] if t["type"] == "subtitles"]
    if len(subtitle_tracks) == 1:
        prop_cmd.extend(["--edit", "track:s1", "--set", "flag-default=1"])
    elif len(subtitle_tracks) > 1:
        for i, track in enumerate(subtitle_tracks, 1):
            props = track["properties"]
            if (
                props.get("language") == "chi"
                and props.get("language_ietf") == "zh-CN"
                and "评论" not in props.get("track_name", "")
            ):
                prop_cmd.extend(["--edit", f"track:s{i}", "--set", "flag-default=1"])
            else:
                prop_cmd.extend(["--edit", f"track:s{i}", "--set", "flag-default=0"])

    # Handle audio tracks
    audio_tracks = [t for t in output_info["tracks"] if t["type"] == "audio"]
    if audio_tracks:
        # Find track with most channels
        max_channels = max(get_channel_count(t) for t in audio_tracks)
        aac_count = 0

        for i, track in enumerate(audio_tracks, 1):
            props = track["properties"]
            codec = track["codec"].lower()
            channels = get_channel_count(track)
            orig_name = props.get("track_name")

            # Set default audio
            if channels == max_channels:
                prop_cmd.extend(["--edit", f"track:a{i}", "--set", "flag-default=1"])
            else:
                prop_cmd.extend(["--edit", f"track:a{i}", "--set", "flag-default=0"])

            # Rename tracks if no original name
            if not orig_name:
                if "flac" in codec:
                    if channels == 2:
                        name = "2ch"
                    elif channels == 3:
                        name = "2.1ch"
                    elif channels == 6:
                        name = "5.1ch"
                    prop_cmd.extend(["--edit", f"track:a{i}", "--set", f"name={name}"])
                elif "aac" in codec:
                    aac_count += 1
                    if aac_count == 1:
                        name = "声优评论"
                    elif aac_count == 2:
                        name = "监督评论"
                    elif aac_count == 3:
                        name = "军事评论"
                    else:
                        name = f"评论 {aac_count}"
                    prop_cmd.extend(["--edit", f"track:a{i}", "--set", f"name={name}"])

    # Execute mkvpropedit
    if len(prop_cmd) > 2:
        print(" ".join(prop_cmd))
        subprocess.run(prop_cmd, check=True)

    if not save_temp_fonts:
        shutil.rmtree(subsetted_dir)
