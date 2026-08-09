#!/usr/bin/env python3
"""מיישר רפליקה בעברית אל חלון הדיבור שהמודל הנפיש.

הרקע: Seedance מנפיש שפתיים משכנעות רק כאשר generate_audio=true, כלומר
רק כשהוא מייצר בעצמו פס קול. אבל העברית שהוא מייצר שגויה — הוא מחקה את
צליל השפה בלי לומר את המילים. אז לוקחים ממנו את התנועה וזורקים את הקול.

הבעיה שנוצרת: אם פשוט מדביקים הקראה תקינה מ-TTS, היא מתחילה ונגמרת
בזמנים אחרים מאלה שבהם הפה זז, והפער בולט לעין.

מה שהסקריפט עושה: מאתר מתוך פס הקול של המודל את החלון שבו הוא באמת
דיבר, ומכווץ או מותח את ההקראה העברית כך שתמלא בדיוק את אותו חלון.
הפה מתחיל לזוז כשהעברית מתחילה ונעצר כשהיא נגמרת.

זה לא סנכרון פונמות — אין כלי כזה כאן. זה יישור גבולות, וזה מה שהופך
דיבוב לאמין: הצופה סולח על צורת פה לא מדויקת, אבל לא על פה שזז כשאין
קול או שותק כשיש.

שימוש:
    python3 scripts/align_voice.py <סרטון_המודל> <הקראה.mp3> <פלט.mp3>
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# ffprobe לא מותקן כאן, אז כל המדידות נעשות דרך ffmpeg בלבד.
FFMPEG = ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg"

# סף העוצמה שמעליו נחשב שיש דיבור. -45dB מפריד דיבור מרעש רקע
# ומהמוזיקה החלשה שהמודל לפעמים מוסיף מעצמו.
SPEECH_FLOOR_DB = -45.0
# רזולוציית הסריקה בשניות. 0.05 מספיק דק כדי לתפוס תחילת מילה.
STEP = 0.05
# גבולות המתיחה. מעבר לזה הקול מתחיל להישמע מעוות.
MIN_TEMPO, MAX_TEMPO = 0.75, 1.35


DURATION_RE = re.compile(r"Duration: (\d+):(\d+):(\d+\.?\d*)")


def duration(path):
    """אורך בשניות, נקרא משורת ה-Duration שffmpeg מדפיס ל-stderr."""
    proc = subprocess.run(
        [str(FFMPEG), "-i", str(path)], capture_output=True, text=True,
    )
    m = DURATION_RE.search(proc.stderr)
    if not m:
        raise RuntimeError(f"לא הצלחתי לקרוא את אורך {path}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def speech_window(video):
    """מחזיר (התחלה, סוף) של הדיבור בפס הקול של המודל, בשניות."""
    total = duration(video)
    # astats על חלונות קצרים נותן עוצמת RMS לאורך הזמן בקריאה אחת.
    proc = subprocess.run(
        [str(FFMPEG), "-v", "error", "-i", str(video),
         "-af", f"astats=metadata=1:reset={max(1, int(STEP * 100))},"
                f"ametadata=print:key=lavfi.astats.Overall.RMS_level",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )

    times, levels = [], []
    pending = None
    for line in proc.stderr.splitlines():
        line = line.strip()
        if line.startswith("frame:"):
            for part in line.split():
                if part.startswith("pts_time:"):
                    pending = float(part.split(":", 1)[1])
        elif "RMS_level=" in line and pending is not None:
            raw = line.split("=", 1)[1]
            try:
                levels.append(float(raw))
                times.append(pending)
            except ValueError:
                pass  # '-inf' על קטע שקט מוחלט
            pending = None

    loud = [t for t, lv in zip(times, levels) if lv > SPEECH_FLOOR_DB]
    if not loud:
        # לא נמצא דיבור — עדיף למלא את כל הסצנה מלנחש חלון שגוי.
        return 0.0, total
    return min(loud), max(loud)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    video, voice, out = (Path(a) for a in sys.argv[1:])

    start, end = speech_window(video)
    target = end - start
    have = duration(voice)
    tempo = have / target if target > 0 else 1.0

    if tempo < MIN_TEMPO or tempo > MAX_TEMPO:
        # מתיחה חריגה תשמע מעוותת. עדיף להשאיר את הקצב הטבעי ולמרכז
        # את ההקראה בתוך החלון — הפער בקצוות קטן מהעיוות שהמתיחה תיצור.
        print(f"  פער גדול מדי למתיחה (x{tempo:.2f}) — ממרכז במקום למתוח")
        start += max(0.0, (target - have) / 2)
        tempo = 1.0

    chain = f"atempo={tempo:.4f}," if abs(tempo - 1.0) > 0.01 else ""
    subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(voice),
         "-af", f"{chain}adelay={int(start * 1000)}:all=1,"
                f"apad,atrim=0:{duration(video):.3f}",
         "-c:a", "libmp3lame", "-q:a", "2", str(out)],
        check=True,
    )

    print(f"  חלון הדיבור של המודל: {start:.2f}s - {end:.2f}s ({target:.2f}s)")
    print(f"  אורך ההקראה: {have:.2f}s, מתיחה: x{tempo:.3f}")
    print(f"  נשמר: {out}")


if __name__ == "__main__":
    main()
