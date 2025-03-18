# 使用 GPT-4o 生成代码

## 第1轮

PV01.mkv: 错误信息如下

```
mkvmerge v88.0 ('All I Know') 64-bit
Warning: More than one name was given for a single attachment. '方正准圆_GBK.MNN27RAV.ttf' will be discarded and '微软雅黑.7KKLB1SW.ttf' used instead.
Error: The type of file 'dist/subsetted/微软雅黑.7KKLB1SW.ttf' could not be recognized.
```

生成的命令：

```bash
mkvmerge -o dist/PV01_final.mkv --no-subtitles --no-audio PV01.mkv --no-audio --no-video --no-chapters PV01.mkv --language 0:zh --track-name 0:Simplified Chinese dist/subsetted/PV01.SC.ass --language 0:zh-TW --track-name 0:Traditional Chinese dist/subsetted/PV01.TC.ass --attachment-name 方正准圆_GBK.MNN27RAV.ttf dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attachment-name 微软雅黑.7KKLB1SW.ttf dist/subsetted/微软雅黑.7KKLB1SW.ttf
```

## 第2轮：

错误信息如下

```
mkvmerge v88.0 ('All I Know') 64-bit
Warning: More than one name was given for a single attachment. '方正准圆_GBK.MNN27RAV.ttf_-7482906316395925147' will be discarded and '微软雅黑.7KKLB1SW.ttf_-1567784702139865755' used instead.
Error: The type of file 'dist/subsetted/微软雅黑.7KKLB1SW.ttf' could not be recognized.
```

生成的命令：

```bash
mkvmerge -o dist/PV01_final.mkv --no-subtitles --no-audio PV01.mkv --no-audio --no-video --no-chapters PV01.mkv --language 0:zh --track-name 0:Simplified Chinese dist/subsetted/PV01.SC.ass --language 0:zh-TW --track-name 0:Traditional Chinese dist/subsetted/PV01.TC.ass --attachment-name 方正准圆_GBK.MNN27RAV.ttf_-7482906316395925147 dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attachment-name 微软雅黑.7KKLB1SW.ttf_-1567784702139865755 dist/subsetted/微软雅黑.7KKLB1SW.ttf
```

错误是 `--attachment-name` 后面同时给了名称和文件地址，而实际上文件地址需要通过 `--attach-file` 传递。

## 第3轮

对话：提供给上面的错误原因

结果程序正常运行，但是生成的视频没有音频轨道，而且两个字幕轨道都被设为默认轨道。

## 第4轮

音频加上了，还有3个问题：

1. 音频轨道没有正确命名
2. 简体中文的语言应设为`zh-CN`
3. 应该只有一个默认字幕轨道（现在两个字幕轨道都是默认轨道）

## 第5轮

上面的问题1和3都没有解决。

原因是程序使用 `mkvmerge -i dist/PV01_final.mkv` 获取文件信息，这个命令的输出信息如下，
```
File 'dist/PV01_final.mkv': container: Matroska
Track ID 0: video (HEVC/H.265/MPEG-H)
Track ID 1: audio (FLAC)
Track ID 2: subtitles (SubStationAlpha)
Track ID 3: subtitles (SubStationAlpha)
Attachment ID 1: type 'font/ttf', size 90656 bytes, file name '方正准圆_GBK.MNN27RAV.ttf'
Attachment ID 2: type 'font/ttf', size 16224 bytes, file name '微软雅黑.7KKLB1SW.ttf'
```
里面没有音频的声道信息，也没有字幕语言的信息。

## 第6轮

还是没有解决。
