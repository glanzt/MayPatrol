#!/usr/bin/env python3
"""מייצר את קובץ הכתוביות מתוך תסריט הדיבור.

    python3 scripts/make_srt.py [scenario/dialogue.tsv] [subtitles/final.srt]

הכתוביות עצמן לא נושאות שם דובר — ילדים בגיל היעד קוראים לאט, ותווית
כמו "מאי:" בתחילת כל שורה גוזלת מקום ומאטה את הקריאה. עמודת הדובר
משמשת רק לניתוב ההקראה לקול הנכון (ראה mix_voice.py).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse(path):
    """קורא את ה-TSV ומחזיר את הרפליקות לפי סדר הזמן."""
    cues = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) != 5:
            sys.exit(f"שגיאה בשורה {lineno}: נדרשות 5 עמודות, נמצאו {len(parts)}")

        scene, start, end, speaker, text = parts
        try:
            start, end = float(start), float(end)
        except ValueError:
            sys.exit(f"שגיאה בשורה {lineno}: זמן לא תקין")

        if end <= start:
            sys.exit(f"שגיאה בשורה {lineno}: זמן הסיום לא אחרי זמן ההתחלה")

        cues.append(
            {
                "scene": int(scene),
                "start": start,
                "end": end,
                "speaker": speaker,
                # \n ב-TSV הוא שבירת שורה בכתובית
                "text": text.replace("\\n", "\n"),
            }
        )

    cues.sort(key=lambda c: c["start"])
    return cues


def check_overlaps(cues):
    """כתוביות חופפות נערמות זו על זו על המסך — עדיף ליפול מאשר לצרוב ככה."""
    for prev, cur in zip(cues, cues[1:]):
        if cur["start"] < prev["end"]:
            sys.exit(
                f"שגיאה: חפיפה בין הכתוביות ב-{prev['start']:.1f}s ו-{cur['start']:.1f}s"
            )


def timestamp(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scenario/dialogue.tsv"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "subtitles/final.srt"

    if not src.exists():
        sys.exit(f"שגיאה: תסריט הדיבור '{src}' לא נמצא")

    cues = parse(src)
    if not cues:
        sys.exit("שגיאה: לא נמצאו רפליקות בתסריט")

    check_overlaps(cues)

    blocks = [
        f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}\n"
        for i, c in enumerate(cues, 1)
    ]

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(blocks), encoding="utf-8")

    speakers = {}
    for c in cues:
        speakers[c["speaker"]] = speakers.get(c["speaker"], 0) + 1
    breakdown = ", ".join(f"{name} {count}" for name, count in sorted(speakers.items()))
    print(f"נוצרו {len(cues)} כתוביות ב-{dst}")
    print(f"רפליקות לפי דובר: {breakdown}")


if __name__ == "__main__":
    main()
