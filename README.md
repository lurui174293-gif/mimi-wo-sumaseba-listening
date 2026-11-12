# 侧耳倾听日语听力页

网页按五段播放用户提供的电影音频，字幕随播放自动滚动，并提供中日对照、假名和部分语法注释。

字幕参考 [Ryuushi712 整理的《侧耳倾听》蓝光中日双语字幕](https://bbs.acgrip.com/thread-7112-1-1.html)：日文及中文基础字幕来自台版蓝光，歌曲翻译和双语时间轴由整理者补充。本站按音频片段重新分段，并生成假名及学习语法。请保留原字幕来源和作者说明。

原始 ASS 文件不收入仓库。若需重新生成 `data.json` 与 `data.js`，将字幕文件放在 `reference_subtitles/official-bilingual.ass`，安装 `pykakasi==2.3.0`，运行 `python build_bilingual.py`。脚本会沿用当前数据的片段边界和语法注释。
