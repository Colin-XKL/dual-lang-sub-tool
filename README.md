# dual-lang-sub-tool

A tool for make and fine-tune bilingual subtitles.

一个简单的双语字幕制作工具

check main.py for details.

place main.py at the same dir of your mkv/mp4 file, use `ffmpeg -i xxx.mp4` to check to subtitle stream id , and modify
the code to update the id, the run it , and it would automaticaly do the extract, merge jobs.

将main.py 放到mkv/mp4资源所在文件夹, 使用ffmpeg -i 确定要提取的stream 的id , 填入py文件中, 执行即可. 会自动提取指定的字幕并合并,
输出到原文件同目录

## Roadmap

- [x] srt merge
- [x] auto extract srt from certain stream
- [ ] auto choose stream to extract subtitle

## LICENSE

MIT
