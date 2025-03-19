# 使用 DeepSeek R1 生成代码

## 第1轮

错误：

```
mkvmerge v88.0 ('All I Know') 64-bit
Error: The file '--track' could not be opened for reading: open file error.
```

实际运行的命令：

```
mkvmerge -o dist/PV01.mkv PV01.mkv --track 1 --default-track 0:1 --track-name 0:2ch --language 0:zho-CN --track-name 0:Chinese (Simplified) dist/subsetted/PV01.SC.ass --language 0:zho-TW --track-name 0:Chinese (Traditional) dist/subsetted/PV01.TC.ass --attach-file dist/subsetted/方正准圆_GBK.MNN27RAV.ttf --attach-file dist/subsetted/微软雅黑.7KKLB1SW.ttf
```

## 第2轮

程序能够正常运行，但是音频轨道没有正确命名，两个字幕轨道都设置为了默认轨道。
