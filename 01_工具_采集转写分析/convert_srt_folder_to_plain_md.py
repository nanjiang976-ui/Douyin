"""Convert a folder of user-supplied SRT subtitles into plain-text Markdown files.

Each output Markdown contains only the subtitle wording: no sequence numbers,
timecodes, headings, or analysis.  The source SRT files are never modified.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TIME_LINE = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?\s+-->\s+\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?.*$"
)
INDEX_LINE = re.compile(r"^\s*\d+\s*$")
TAG = re.compile(r"<[^>]+>|\{\\[^}]+\}")
ILLEGAL_FILENAME = re.compile(r'[<>:"/\\|?*]')


def read_srt(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"无法识别字幕编码：{path}")


def subtitle_lines(srt_text: str) -> list[str]:
    lines: list[str] = []
    for raw in srt_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        text = TAG.sub("", raw).strip()
        if not text or INDEX_LINE.fullmatch(text) or TIME_LINE.fullmatch(text):
            continue
        lines.append(text)
    return lines


def plain_transcript(lines: list[str]) -> str:
    # Auto-generated subtitles often omit punctuation.  Preserve each cue as a
    # line so the Markdown remains plain text while retaining spoken rhythm.
    return "\n".join(lines).strip() + "\n"


def safe_stem(path: Path) -> str:
    stem = ILLEGAL_FILENAME.sub("_", path.stem).strip(" ._")
    return stem or "未命名文案"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert SRT files to plain-text Markdown.")
    parser.add_argument("source", type=Path, help="Folder containing SRT files")
    parser.add_argument("output", type=Path, help="Folder for plain-text Markdown files")
    args = parser.parse_args()

    srt_files = sorted(args.source.glob("*.srt"), key=lambda path: path.name.lower())
    if not srt_files:
        raise SystemExit(f"未找到 SRT 文件：{args.source}")
    args.output.mkdir(parents=True, exist_ok=True)

    written = 0
    for index, source_path in enumerate(srt_files, start=1):
        transcript = plain_transcript(subtitle_lines(read_srt(source_path)))
        if not transcript.strip():
            raise ValueError(f"字幕正文为空：{source_path.name}")
        target = args.output / f"{index:02d}_{safe_stem(source_path)}.md"
        target.write_text(transcript, encoding="utf-8", newline="\n")
        written += 1

    print(f"converted={written} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
