# 使用 DeepSeek V3 生成代码

## 第1轮

错误：

```
  File "/root/mkv-merge/gup/generated-DeepSeekV3.py", line 47, in <module>
    subtitles_dir.glob("*.[oO][tT][fF]")
TypeError: unsupported operand type(s) for +: 'generator' and 'generator'
```

## 第2轮

程序能够正常运行，但是音频轨道没有正确命名，两个字幕轨道都设置为了默认轨道。

## 第3轮

问题和上一轮一样。

## 第4轮

对话：要求使用 `mkvmerge -J` 而不是 `mkvinfo`。

这回音频轨道的名称对了，默认字幕轨道的问题还是没有解决。

## 第5/6/7轮

对话：要求合并后单独修改默认字幕轨道。

问题还是没有解决。

# 第8/9轮

对话，更正字幕轨道设置。
