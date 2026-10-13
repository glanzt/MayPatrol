# רצף ההיפתחות בסגנון איירון מן

הרובוט ההומנואידי נפתח, ומאי מתגלה בפנים.

מקור: צילום של רובוט הומנואידי תלוי על עגורן גנטרי במעבדה.
הצילום משמש כפריים פתיחה, בדיוק כמו בסצנת הסלטה — העולם לא נוצר
מחדש, הוא נמשך מהתמונה האמיתית.

## למה שני שוטים ולא אחד

ההיפתחות וההתגלות הן שתי בקשות קשות שמושכות לכיוונים מנוגדים:
הראשונה דורשת שהמודל ישמור על הרובוט מדויק תוך כדי שהוא מפרק אותו,
השנייה דורשת שיכניס פנים אנושיות מזוהות לתוך אותו פריים. ניסיון
לעשות את שתיהן בשוט אחד בדרך כלל מקבל אחת מהן ומוותר על השנייה.

לכן: שוט א' פותח את החזה ועוצר על החלל המואר. שוט ב' מתחיל מהפריים
האחרון של שוט א' ומגלה את מאי. מחברים אותם כמו שחיברנו את הטרמפולינה.

## שוט א' — ההיפתחות

```
mode: omni_reference
model: seedance_2_5
medias: [{ role: start_image, value: <תמונת הרובוט> }]
aspect_ratio: 9:16
duration: 5
resolution: 720p
generate_audio: true
```

Continue exactly from the starting frame with no change to the
environment — the same humanoid robot hanging in its harness from the
black gantry crane with the yellow winch and red hook, the same lab room
with metal shelving, cardboard boxes, grey carpet and white walls,
identical camera position and framing.

ACTION: the robot powers up. Its eye visor flares bright electric blue.
Seams of light crack open across its white chest plate, and the armoured
chest panels split along those seams and rotate outward and back on
precise mechanical hinges, layer peeling away from layer, like an Iron
Man suit opening. Brilliant blue-white light pours out of the opening
cavity in volumetric shafts, flooding the room. The shoulder and
abdominal plates retract in sequence. The chest is fully open at the end,
a glowing hollow cockpit where the torso was, nobody visible inside yet.

AUDIO: heavy servo whirs, pneumatic hiss, metallic clanks, a rising
electrical hum. No speech.

Style: photorealistic, real lab lighting plus the blue glow, matching the
grain and colour of the starting frame exactly. Smooth precise mechanical
motion, no morphing, no distortion.

## שוט ב' — ההתגלות

`start_image` הוא הפריים האחרון של שוט א'. הצילומים של מאי נכנסים
כ-`image_references` כדי לנעול את הזהות שלה.

ACTION: the blue light inside the open chest cavity softens, and seated
inside the cockpit is the young girl from the reference photographs — the
same real child, photorealistic, wearing a sleek dark pilot suit with
glowing blue trim. She is strapped into a small moulded seat with a
control yoke in front of her. She looks up into camera and breaks into a
huge triumphant grin, then raises one fist in the air. The camera pushes
slowly in on her face. Her facial identity stays locked to the reference
photographs.

AUDIO: a soft electrical hum and a single bright chime. No speech.

## מה לבדוק כשזה חוזר

- האם הרובוט נשאר הרובוט מהצילום, או שהמודל המציא אחד אחר.
- האם הפתח גדול מספיק שמאי תיכנס בו בלי להיראות מודבקת.
- חיבור בין השוטים: הפריים האחרון של א' והראשון של ב' חייבים להתאים.
