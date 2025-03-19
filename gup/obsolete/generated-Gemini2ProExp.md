# 使用 Gemini 2 Pro Experimental 02-05 生成代码

## 第1轮

错误：

```
Traceback (most recent call last):
  File "/root/mkv-merge/gup/generated-Gemini2ProExp.py", line 294, in <module>
    main()
  File "/root/mkv-merge/gup/generated-Gemini2ProExp.py", line 290, in main
    rename_aac_tracks(output_mkv)
  File "/root/mkv-merge/gup/generated-Gemini2ProExp.py", line 237, in rename_aac_tracks
    audio_tracks = get_track_info(mkv_file, "audio")
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/mkv-merge/gup/generated-Gemini2ProExp.py", line 25, in get_track_info
    for track in info["tracks"]:
                 ~~~~^^^^^^^^^^
KeyError: 'tracks'
```

生成的command是

```bash
mkvmerge -o dist/PV01_merged.mkv -d 0 PV01.mkv -D --no-chapters PV01.mkv -d 0 -a 1 --default-track 1:yes --language 0:zho --track-name 0:简体中文 dist/subsetted/PV01.SC.ass --language-ietf 0:zh-CN --default-track 0:yes --language 1:zho --track-name 1:繁体中文 dist/subsetted/PV01.TC.ass --language-ietf 1:zh-TW --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/微软雅黑.7KKLB1SW.ttf
```

使用了错误的 `--language-ietf` 选项。

## 第2轮

对话：提供给了上面的错误信息，以及错误选项说明。

程序成功运行，输出如下

```
执行的命令: mkvmerge -o dist/PV01_merged.mkv -d 0 PV01.mkv -D --no-chapters PV01.mkv -d 0 -a 1 --default-track 1:yes --language 0:zho --track-name 0:简体中文 dist/subsetted/PV01.SC.ass --default-track 0:yes --language 1:zho --track-name 1:繁体中文 dist/subsetted/PV01.TC.ass --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/微软雅黑.7KKLB1SW.ttf
mkvmerge 错误输出:
```

但是生成的mkv有三个问题：
1. 多了一个音频轨道，生成的mkv有两个完全一样的音频轨道
2. 音频轨道没有设置名称
3. 简体中文字幕轨道的名称是正确的，但是繁体中文字幕轨道没有设置名称

## 第3轮

对话：提供给了输出信息，和三个问题说明。


程序成功运行，输出如下
```
执行的命令: mkvmerge -o dist/PV01_merged.mkv -d 0 PV01.mkv -D --no-chapters PV01.mkv -d 0 -a 1 --default-track 1:yes --track-name 1:Unknown Channels --language 0:zho --track-name 0:简体中文 dist/subsetted/PV01.SC.ass --default-track 0:yes --language 1:zho --track-name 1:繁体中文 dist/subsetted/PV01.TC.ass --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attachment-mime-type application/x-truetype-font --attach-file dist/subsetted/微软雅黑.7KKLB1SW.ttf
mkvmerge 错误输出:
```

结果上面的三个问题一个也没有解决。

## 第4轮

还是一个问题也没有解决。。。

## 放弃。。。
