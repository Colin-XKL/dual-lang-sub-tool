# dual-lang-sub-tool

A tool for make and fine-tune bilingual subtitles.

一个简单的双语字幕制作工具

check main.py for details.

place main.py at the same dir of your mkv/mp4 file, use `ffmpeg -i xxx.mp4` to check to subtitle stream id , and modify
the code to update the id, the run it , and it would automaticaly do the extract, merge jobs.

将main.py 放到mkv/mp4资源所在文件夹, 使用ffmpeg -i 确定要提取的stream 的id , 填入py文件中, 执行即可. 会自动提取指定的字幕并合并,
输出到原文件同目录


Docker Image: (amd64 & arm64 support)

- ghcr.io/colin-xkl/dual-lang-sub-tool
- colinxkl/dual-lang-sub-tool



## Example

step 1: 使用ffmpeg -i 视频文件路径, 来查看这些文件是否内建了字幕,以及它们对应的stream id.

`ffmpeg -i ./Solar.Opposites.S05E01.2024.1080p.DSNP.WEB-DL.H264.DDP5.1-ADWeb.mkv`


```
  Stream #0:9(eng): Subtitle: subrip
    Metadata:
      title           : English
      BPS             : 129
      DURATION        : 00:22:38.982000000
      NUMBER_OF_FRAMES: 588
      NUMBER_OF_BYTES : 21927

    ...

  Stream #0:24(chi): Subtitle: subrip (default)
    Metadata:
      title           : Chinese Simplified
      BPS             : 116
      DURATION        : 00:21:35.335000000
      NUMBER_OF_FRAMES: 451
      NUMBER_OF_BYTES : 18932
```

可以看到视频有内建的简体中文字幕, 索引 stream id 24. 英文字幕索引  stream id 9.


如果你不方便或不想安装ffmpeg, 可以使用本项目对应的docker镜像, 其内置有ffmpeg工具. 使用方式为
``` bash
cd /media/tvshow/Loki_S02 # 替换为你要处理的视频文件目录
sudo docker run -it --rm -v ./:/media:ro colinxkl/dual-lang-sub-tool dual_sub_tool --check /media
```

step 2: 在视频文件同目录下, 新建一个文本文件, 名为`dual_sub_conf.yaml`. 仓库根目录有个示例. 格式如下:
```yaml
first_line_sub:
  track_num: 24
  lang_code: "chi"

sencond_line_sub: 
  track_num: 9
  lang_code: "eng"

file_extensions:
  - "mkv"
  - "mp4"
```

step 3: 执行命令
```bash
cd /media/tvshow/Loki_S02 # 替换为你要处理的视频文件目录
sudo docker run -it --rm -v ./:/media colinxkl/dual-lang-sub-tool dual_sub_tool /media 
```

step 4: 完成, 在目标文件夹下你应该能看到生成的srt文件, 选择性检查下, 确认没有问题后, 你就可以开始享受你的资源了 😎


## Roadmap

- [x] srt merge
- [x] auto extract srt from certain stream
- [ ] auto choose stream to extract subtitle

## LICENSE

MIT
