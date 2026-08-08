#!/usr/bin/env bash
# מתקין ffmpeg סטטי (כולל libass + libfribidi לתמיכה בעברית מימין לשמאל).
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg כבר מותקן: $(command -v ffmpeg)"
  exit 0
fi

echo "מתקין ffmpeg-static..."
npm install ffmpeg-static --silent

FF="$(node -e "console.log(require('ffmpeg-static'))")"
echo "ffmpeg הותקן ב: $FF"

# בדיקה שהתמיכה בעברית קיימת
if ! "$FF" -version 2>&1 | grep -q -- '--enable-libass'; then
  echo "אזהרה: ffmpeg נבנה ללא libass — כתוביות צרובות לא יעבדו." >&2
  exit 1
fi
if ! "$FF" -version 2>&1 | grep -q -- '--enable-libfribidi'; then
  echo "אזהרה: ffmpeg נבנה ללא libfribidi — סדר האותיות בעברית יהיה שגוי." >&2
  exit 1
fi

echo "תקין: libass + libfribidi זמינים. כתוביות בעברית ייצרבו נכון."
