#!/usr/bin/env bash
# מרכיב את הסרטון הסופי: מחבר את כל הקטעים מ-clips/ וצורב כתוביות בעברית.
#
# שימוש:
#   ./scripts/build_video.sh [קובץ_כתוביות] [קובץ_פלט]
#
# ברירת מחדל: subtitles/final.srt -> output/final.mp4
#
# הקטעים ב-clips/ מעובדים לפי סדר אלפביתי, ולכן יש למספר אותם:
#   clips/01_opening.mp4, clips/02_rescue.mp4, ...

set -euo pipefail

cd "$(dirname "$0")/.."

SRT="${1:-subtitles/final.srt}"
OUT="${2:-output/final.mp4}"

# --- הגדרות ---
# 854x480 הוא הרזולוציה המקורית של הקטעים שיוצאים מ-Seedance 2.5 ב-480p.
# פלט בגודל הזה נמנע ממתיחה: הגדלה ל-1080p מנפחת את הקובץ פי כמה בלי
# להוסיף ולו פרט אחד, והסרטון מיועד לצפייה בטלפון.
# גודל הכתוביות מתכווץ אוטומטית יחסית לגובה (ראה scripts/make_ass.py).
WIDTH=854
HEIGHT=480
FPS=24
# עוצמת מוזיקת הרקע ביחס לדיבור. 0.18 מספיק כדי שתורגש בלי להתחרות
# בקול. להעלות ל-0.3 למוזיקה בולטת יותר, להוריד ל-0.1 לרמז בלבד.
MUSIC_VOLUME=0.18
# עיצוב הכתוביות (פונט, גודל, שוליים) מוגדר ב-scripts/make_ass.py

# --- איתור ffmpeg ---
if command -v ffmpeg >/dev/null 2>&1; then
  FF="ffmpeg"
elif [ -f node_modules/ffmpeg-static/ffmpeg ]; then
  FF="$(pwd)/node_modules/ffmpeg-static/ffmpeg"
else
  echo "שגיאה: ffmpeg לא נמצא. הרץ קודם ./scripts/setup.sh" >&2
  exit 1
fi

# --- בדיקות קלט ---
shopt -s nullglob
CLIPS=(clips/*.mp4)
shopt -u nullglob

if [ ${#CLIPS[@]} -eq 0 ]; then
  echo "שגיאה: לא נמצאו קטעים בתיקייה clips/" >&2
  exit 1
fi

if [ ! -f "$SRT" ]; then
  echo "שגיאה: קובץ הכתוביות '$SRT' לא נמצא" >&2
  exit 1
fi

mkdir -p output .build
rm -f .build/*.mp4 .build/concat.txt

echo "נמצאו ${#CLIPS[@]} קטעים. מנרמל..."

# --- שלב 1: נרמול כל הקטעים לאותה רזולוציה/פריימרייט ---
# בלי זה החיבור נכשל או יוצא משובש כשהקטעים מגיעים ממודלים שונים.
i=0
for clip in "${CLIPS[@]}"; do
  i=$((i + 1))
  out=$(printf ".build/%03d.mp4" "$i")

  # --- איתור ההקראה של הסצנה ---
  # ההתאמה נעשית לפי הקידומת המספרית של הקטע: clips/01_opening.mp4
  # מקבל את ההקראה voice/01.mp3. כך אפשר לשנות שמות קטעים בלי לשבור
  # את ההתאמה, וסצנה בלי הקראה פשוט תישאר שקטה.
  prefix="$(basename "$clip" | cut -d_ -f1)"
  narration=""
  for ext in mp3 m4a wav aac; do
    if [ -f "voice/${prefix}.${ext}" ]; then
      narration="voice/${prefix}.${ext}"
      break
    fi
  done

  if [ -n "$narration" ]; then
    printf "  [%d/%d] %s  ← %s\n" "$i" "${#CLIPS[@]}" "$clip" "$narration"
    # apad מאריך את ההקראה בשקט עד סוף הקטע. בלעדיו -shortest היה
    # חותך את הווידאו באורך ההקראה, שקצרה בדרך כלל מ-8 השניות.
    AUDIO_INPUT=(-i "$narration")
    AUDIO_FILTER="apad"
  else
    printf "  [%d/%d] %s  (ללא הקראה)\n" "$i" "${#CLIPS[@]}" "$clip"
    # פס קול שקט — שומר על סנכרון בחיבור גם בסצנות בלי דיבור
    AUDIO_INPUT=(-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000)
    AUDIO_FILTER="anull"
  fi

  "$FF" -y -loglevel error \
    -i "$clip" \
    "${AUDIO_INPUT[@]}" \
    -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=${FPS}" \
    -af "$AUDIO_FILTER" \
    -map 0:v:0 -map "1:a:0" \
    -shortest \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -ar 48000 -ac 2 \
    "$out"

  echo "file '$(pwd)/$out'" >> .build/concat.txt
done

# --- שלב 2: חיבור הקטעים ---
echo "מחבר את הקטעים..."
"$FF" -y -loglevel error -f concat -safe 0 -i .build/concat.txt \
  -c copy .build/merged.mp4

# --- שלב 3: צריבת כתוביות בעברית ---
# libass + libfribidi מטפלים אוטומטית בסדר מימין לשמאל.
# הטקסט ב-SRT נכתב בסדר לוגי רגיל — אין צורך להפוך אותיות ידנית.
#
# ההמרה ל-ASS נעשית דרך make_ass.py ולא ישירות מ-SRT: ffmpeg קובע ל-SRT
# רזולוציית ייחוס של 384x288, ולכן גודל הפונט היה מתנפח פי 3.75 על פריים 1080p.
echo "מכין את קובץ הכתוביות..."
python3 scripts/make_ass.py "$SRT" .build/subs.ass "$WIDTH" "$HEIGHT"

echo "צורב כתוביות בעברית..."
"$FF" -y -loglevel error -i .build/merged.mp4 \
  -vf "ass=.build/subs.ass" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy \
  .build/subtitled.mp4

# --- שלב 4: מוזיקת רקע (אופציונלי) ---
# הקובץ הראשון שנמצא ב-music/ מנוגן מתחת לכל הסרטון.
shopt -s nullglob
MUSIC=(music/*.mp3 music/*.m4a music/*.wav music/*.aac)
shopt -u nullglob

if [ ${#MUSIC[@]} -eq 0 ]; then
  mv .build/subtitled.mp4 "$OUT"
else
  echo "מוסיף מוזיקת רקע: ${MUSIC[0]}"
  # aloop מאריך את המוזיקה אם היא קצרה מהסרטון, ו-volume מנמיך אותה
  # כדי שלא תתחרה בדיבור. sidechaincompress מוריד אותה עוד קצת בכל
  # פעם שדמות מדברת ("ducking"), ומחזיר אותה בין הרפליקות.
  "$FF" -y -loglevel error -i .build/subtitled.mp4 -i "${MUSIC[0]}" \
    -filter_complex "\
      [1:a]aloop=loop=-1:size=2e9,volume=${MUSIC_VOLUME},aformat=sample_rates=48000:channel_layouts=stereo[bg]; \
      [0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[voice][key]; \
      [bg][key]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=600[ducked]; \
      [voice][ducked]amix=inputs=2:normalize=0:duration=first[out]" \
    -map 0:v:0 -map "[out]" \
    -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
    "$OUT"
fi

# --- סיכום ---
# ffmpeg -i ללא קובץ פלט מסיים בקוד שגיאה 1 — ה-|| true מונע נפילה בגלל pipefail
DURATION=$({ "$FF" -i "$OUT" 2>&1 | grep -o 'Duration: [0-9:.]*' | cut -d' ' -f2; } || true)
echo ""
echo "הסרטון מוכן: $OUT"
echo "אורך: $DURATION"
