# 使用 Grok 3 生成代码

## 第1轮

PV01.mkv: 成功！

cmd: `['mkvmerge', '-o', 'dist/PV01.mkv', 'PV01.mkv', '--language', '0:zh', '--sub-charset', '0:UTF-8', '--track-name', '0:简体中文', 'dist/subsetted/PV01.SC.ass', '--language', '0:zh', '--sub-charset', '0:UTF-8', '--track-name', '0:繁體中文', 'dist/subsetted/PV01.TC.ass', '--attachment-mime-type', 'application/x-truetype-font', '--attach-file', 'dist/subsetted/方正准圆_GBK.MNN27RAV.ttf', '--attach-file', 'dist/subsetted/微软雅黑.7KKLB1SW.ttf']`

prop_cmd: `['mkvpropedit', 'dist/PV01.mkv', '--edit', 'track:s1', '--set', 'flag-default=0', '--edit', 'track:s2', '--set', 'flag-default=0', '--edit', 'track:a1', '--set', 'flag-default=1', '--edit', 'track:a1', '--set', 'name=2ch']`

可见 Grok3 将制作过程分成了2步，先合并文件，在对轨道进行修改。

一点瑕疵是语言都设置成了`zh`，没有区分`zh-CN`和`zh-TW`，但是字幕轨道的名称是对的。

还有一个问题，是没有设置默认的字幕轨道，原因是 `mkvmerge` 默认使用 `chi` 而不是 `zh` 作为中文的语言代码。

这些也很容易就能手动修正。
