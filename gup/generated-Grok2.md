# 使用 Grok 2 生成代码

## 第1轮

PV01.mkv: 错误信息如下

```
Traceback (most recent call last):
  File "/root/mkv-merge/gup/generated-Grok2.py", line 182, in <module>
    main()
  File "/root/mkv-merge/gup/generated-Grok2.py", line 171, in main
    set_default_tracks(tracks)
  File "/root/mkv-merge/gup/generated-Grok2.py", line 47, in set_default_tracks
    subtitles = [t for t in tracks if t["type"] == "subtitles"]
                                      ~^^^^^^^^
KeyError: 'type'
```

## 第2轮

对话：要求使用 json 格式进行查询。

错误信息如下

```
Traceback (most recent call last):
  File "/root/mkv-merge/gup/generated-Grok2.py", line 181, in <module>
    main()
  File "/root/mkv-merge/gup/generated-Grok2.py", line 85, in main
    "codec": track["properties"]["codec"],
             ~~~~~~~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'codec'
```
