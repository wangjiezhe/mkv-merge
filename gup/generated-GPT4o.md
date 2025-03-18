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
