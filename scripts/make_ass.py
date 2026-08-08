#!/usr/bin/env python3
"""ממיר SRT ל-ASS עם רזולוציה מפורשת, כדי שגודל הפונט יהיה בפיקסלים אמיתיים.

ffmpeg ממיר SRT ל-ASS עם PlayRes של 384x288 כברירת מחדל. libass מותח את
התוצאה לגובה הווידאו, ולכן Fontsize=42 הופך ל-157 פיקסלים על פריים 1080p —
כתוביות ענקיות שמכסות חצי מסך. הפתרון הוא לקבוע PlayRes זהה לרזולוציית
הווידאו, ואז Fontsize נמדד בפיקסלים אמיתיים.

שימוש:
    python3 scripts/make_ass.py <קלט.srt> <פלט.ass> [רוחב] [גובה]
"""

import re
import sys

FONT = "DejaVu Sans"
FONTSIZE = 52          # פיקסלים אמיתיים על פריים 1080p (~4.8% מהגובה)
OUTLINE = 3.5
SHADOW = 1.5
MARGIN_V = 70
MARGIN_H = 140         # שוליים רחבים — שומרים על שורות קצרות וקריאות

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,{mh},{mh},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def to_ass_time(h, m, s, ms):
    """ASS משתמש בשעה בספרה אחת ובמאיות שנייה."""
    return f"{int(h)}:{int(m):02d}:{int(s):02d}.{int(ms) // 10:02d}"


def parse_srt(text):
    # מסירים BOM ומנרמלים סופי שורה כדי שהפיצול לבלוקים יעבוד
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        # שורת המספר הסידורי אופציונלית
        if lines[0].strip().isdigit():
            lines = lines[1:]
        if not lines:
            continue
        match = TIME_RE.search(lines[0])
        if not match:
            continue
        g = match.groups()
        start = to_ass_time(*g[:4])
        end = to_ass_time(*g[4:])
        # \N הוא מעבר שורה מאולץ ב-ASS
        body = "\\N".join(ln.strip() for ln in lines[1:])
        if body:
            cues.append((start, end, body))
    return cues


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    src, dst = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1080

    # גודל הפונט והשוליים מתייחסים ל-1080p ומותאמים יחסית לגבהים אחרים
    scale = height / 1080

    with open(src, encoding="utf-8") as fh:
        cues = parse_srt(fh.read())

    if not cues:
        print(f"שגיאה: לא נמצאו כתוביות תקינות ב-{src}", file=sys.stderr)
        return 1

    out = [
        HEADER.format(
            width=width,
            height=height,
            font=FONT,
            size=round(FONTSIZE * scale),
            outline=round(OUTLINE * scale, 1),
            shadow=round(SHADOW * scale, 1),
            mh=round(MARGIN_H * scale),
            mv=round(MARGIN_V * scale),
        )
    ]
    for start, end, body in cues:
        out.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{body}")

    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")

    print(f"נוצרו {len(cues)} כתוביות ב-{dst} ({width}x{height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
