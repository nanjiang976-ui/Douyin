# 工具说明

这个文件夹里的脚本是之前跑通过的抖音采集和转写工具雏形。

## 脚本用途

- `douyin_profile_extract.js`：连接本地 Edge 调试端口，打开抖音主页或视频页，抓取页面文本、视频链接和接口响应。
- `collect_public_transcripts.py`：按脚本内置账号和候选视频列表，下载公开视频并使用 `faster_whisper` 离线转写。
- `transcribe_extracted_video.py`：从单个视频抓取结果 JSON 中提取视频信息，下载视频并转写。
- `download_visual_checks.py`：下载部分图文/封面素材，用于肉眼核对。
- `screen_low_position_stocks.py`：A 股 AI 应用端、CPU 相关低位筛选脚本，属于 BKISBK 研究时的衍生产物。
- `screen_bk_ai_application_leaders.py`：AI 应用公司技术形态筛选脚本，属于 BKISBK 研究时的衍生产物。

## 复用提示

当前脚本里仍有一些历史任务参数，例如固定的 `SEC_USER_ID`、候选视频 ID 和输出文件名。用于新博主前，建议先把账号 ID、输出目录和候选视频范围改成参数，避免产出混到工具目录里。

更稳妥的长期流程是：一个博主一个账号项目文件夹，抓取原始数据、原始视频、转写文本和分析产出都写入该账号自己的子目录。
