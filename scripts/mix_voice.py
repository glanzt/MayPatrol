#!/usr/bin/env python3
"""ממזג את הרפליקות של כל סצנה לפס קול אחד.

    python3 scripts/mix_voice.py [scenario/dialogue.tsv]

קלט:  voice/lines/NNN.mp3 — הקראה לכל רפליקה, ממוספרת כמו ב-SRT.
פלט:  voice/NN.mp3        — פס קול אחד לכל סצנה, שאותו build_video.sh צורב.

למה צריך את זה בכלל: build_video.sh מצפה לקובץ אחד לכל סצנה ומניח אותו
בתחילתה. ברגע שסצנה מכילה יותר מרפליקה אחת — קריין ואז מאי, למשל —
צריך למקם כל רפליקה בזמן שלה בתוך הסצנה. זה מה שקורה כאן, כדי
ש-build_video.sh יישאר פשוט.

כל רפליקה מתחילה בדיוק בזמן שבו הכתובית שלה מופיעה, כך שהדיבור
והכתוביות מסונכרנים.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENE_DURATION = 8.0  # חייב להתאים לאורך הסצנה בתסריט

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_srt import parse  # noqa: E402


def find_ffmpeg():
    bundled = ROOT / "node_modules/ffmpeg-static/ffmpeg"
    if bundled.exists():
        return str(bundled)
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0:
        return "ffmpeg"
    sys.exit("שגיאה: ffmpeg לא נמצא. הרץ קודם ./scripts/setup.sh")


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scenario/dialogue.tsv"
    if not src.exists():
        sys.exit(f"שגיאה: תסריט הדיבור '{src}' לא נמצא")

    ff = find_ffmpeg()
    lines_dir = ROOT / "voice/lines"
    out_dir = ROOT / "voice"
    out_dir.mkdir(parents=True, exist_ok=True)

    cues = parse(src)

    # מקבץ את הרפליקות לפי סצנה, ושומר את מספר הרפליקה כדי לאתר את הקובץ
    scenes = {}
    for idx, cue in enumerate(cues, 1):
        scenes.setdefault(cue["scene"], []).append((idx, cue))

    built, skipped = 0, []

    for scene in sorted(scenes):
        entries = scenes[scene]
        scene_start = (scene - 1) * SCENE_DURATION

        present = [(i, c) for i, c in entries if (lines_dir / f"{i:03d}.mp3").exists()]
        if not present:
            skipped.append(scene)
            continue

        inputs, filters, labels = [], [], []
        for n, (idx, cue) in enumerate(present):
            offset_ms = round((cue["start"] - scene_start) * 1000)
            if offset_ms < 0:
                sys.exit(f"שגיאה: רפליקה {idx} מתחילה לפני הסצנה שלה")

            inputs += ["-i", str(lines_dir / f"{idx:03d}.mp3")]
            # adelay מזיז את הרפליקה למקומה; all=1 מחיל על שני הערוצים
            filters.append(f"[{n}:a]adelay={offset_ms}:all=1[d{n}]")
            labels.append(f"[d{n}]")

        # amix ממצע את הערוצים, ולכן normalize=0 — אחרת רפליקה בודדת
        # בסצנה עם שתי רפליקות הייתה נחלשת בחצי.
        filters.append(
            f"{''.join(labels)}amix=inputs={len(present)}:normalize=0,"
            f"apad,atrim=0:{SCENE_DURATION}[out]"
        )

        dst = out_dir / f"{scene:02d}.mp3"
        cmd = (
            [ff, "-y", "-loglevel", "error"]
            + inputs
            + ["-filter_complex", ";".join(filters), "-map", "[out]",
               "-c:a", "libmp3lame", "-q:a", "2", str(dst)]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"שגיאה במיזוג סצנה {scene}:\n{result.stderr}")

        speakers = ", ".join(c["speaker"] for _, c in present)
        missing = len(entries) - len(present)
        note = f"  (חסרות {missing} רפליקות)" if missing else ""
        print(f"  סצנה {scene:02d}: {len(present)} רפליקות — {speakers}{note}")
        built += 1

    print(f"\nנוצרו {built} פסי קול ב-{out_dir}")
    if skipped:
        print(f"סצנות ללא הקראה: {', '.join(str(s) for s in skipped)}")


if __name__ == "__main__":
    main()
