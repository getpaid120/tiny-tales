#!/usr/bin/env python3
"""
YouTube Automation Pipeline - Free & Open Source
Produces and uploads one short video daily for a faceless YouTube channel.

Requirements:
  pip install google-generativeai gtts Pillow PyYAML python-dotenv moviepy
  ffmpeg (system)
  Optional: Gemini API key (free from aistudio.google.com)
"""

import os
import json
import yaml
import random
import logging
import subprocess
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("youtube-auto")

load_dotenv()
BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.yaml"
DATA_PATH = BASE / "data.json"

AUDIO_DIR = BASE / "audio"
VIDEO_DIR = BASE / "videos"
THUMB_DIR = BASE / "thumbnails"
ASSETS_DIR = BASE / "assets"
SCRIPTS_DIR = BASE / "scripts"
DASHBOARD_DIR = BASE / "dashboard"

for d in [AUDIO_DIR, VIDEO_DIR, THUMB_DIR, ASSETS_DIR, SCRIPTS_DIR, DASHBOARD_DIR]:
    d.mkdir(exist_ok=True)


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_data():
    """Load persistent data (tracking stats)."""
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            return json.load(f)
    return {
        "total_videos": 0,
        "videos": [],
        "current_streak": 0,
        "last_upload": None,
        "created": datetime.now().isoformat()
    }


def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ─── GENERATE SCRIPT ───────────────────────────────────────────────────

def generate_script(config):
    """Generate a children's story using Gemini or fallback."""
    # Pick a random category and theme
    categories = list(config["story_themes"].keys())
    weights = [0.4, 0.35, 0.25]  # morals most common, then fairy tales, then bedtime
    category = random.choices(categories, weights=weights, k=1)[0]
    theme = random.choice(config["story_themes"][category])

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(config["gemini"]["model"])
            prompt = f"""Write a short children's story for a 50-second YouTube Shorts video.
Category: {category}
Theme: {theme}

Requirements:
- Write exactly 80-100 words
- Simple vocabulary for ages 3-8
- End with a clear takeaway or moral
- Use characters like animals, kids, or magical creatures
- Make it warm and engaging

Return ONLY the story text, nothing else."""
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text:
                return text, category, theme
        except Exception as e:
            log.warning(f"Gemini failed: {e}")

    return fallback_script(category, theme), category, theme


def fallback_script(category, theme):
    """10 diverse built-in stories - one per theme in each category."""
    stories = {
        "morals": [
            "Sammy the squirrel loved his shiny acorn collection. When his friend Oliver asked to play with one, Sammy said no. But playing alone was boring. The next day, Sammy shared his acorns and they built the biggest fort ever. Sharing made everything twice as fun!",
            "Lily wanted to learn the piano right away. But her fingers stumbled and she grew frustrated. \"Why can't I play like Mama?\" she cried. Her mother smiled. \"Every master was once a beginner.\" Lily practiced a little every day, and soon her song was beautiful.",
            "Tommy broke his sister's crayon by accident. He hid the pieces under the rug. But hiding felt worse than telling. He brought his sister a new box of crayons and said sorry. She hugged him. \"I'm not mad. You told the truth.\"",
            "Maya found a penny on the ground. \"Finders keepers!\" she grinned. But then she saw a little boy crying nearby. \"Did you lose something?\" she asked. He nodded. She gave him the penny and his whole face lit up. That smile was worth more than a penny.",
            "Grandpa always said please and thank you. Leo thought it was silly. But when Leo said please to the bus driver, the driver smiled wide. When he thanked the lunch lady, she gave him an extra cookie. Manners were like magic that made everyone feel good!",
            "Pip the penguin saw a baby seal stuck on an ice block. Pip wanted to keep playing, but the seal needed help. Pip pushed the ice block all the way to the water. The seal splashed happily. Helping others was more fun than any game.",
            "Daisy agreed to water her neighbor's plants. For three days she remembered. On the fourth day, she almost forgot. \"I made a promise,\" she said, and ran to water them. The flowers bloomed bright pink. Being responsible made beautiful things happen.",
            "Rex the raccoon was scared of the big slide. All his friends went down whooshing and laughing. Rex took a deep breath. \"You can do this,\" he whispered. He climbed up, closed his eyes, and slid down. It was the best feeling ever!",
            "Peacock Pablo loved his beautiful tail. \"Look at me!\" he cried, shaking his feathers. But the other animals grew tired of his showing off. Pablo felt lonely. \"I'm sorry,\" he said softly. His friends forgave him, and they played together again.",
            "The ants were moving a giant crumb up a hill. It was too heavy for one ant. But when they all pushed together, the crumb moved inch by inch. \"Teamwork!\" they cheered. Alone we can do little, together we can do so much."
        ],
        "fairy_tales": [
            "In the Whispering Woods, every tree had a secret. Little Fern followed a trail of glowing mushrooms to a fairy door. She knocked softly. \"Hello?\" The door opened, and a tiny fairy offered her a cup of starlight tea. \"Thank you for believing,\" said the fairy.",
            "Princess Elara never wore a crown. She wore muddy boots and helped every creature in the kingdom. When a lost dragon cried at her door, she didn't run. She gave it a blanket and named it Sparkle. The dragon became her kindest friend.",
            "Sir Wally wasn't tall or strong. He was small and terrified of spiders. But when the village cat got stuck in a tree, Wally climbed up rung by shaking rung. He saved the cat. \"Real bravery,\" said the king, \"is doing it even when you're scared.\"",
            "In the meadow of Mumblebrook, the animals could talk — but only if you were kind. A rabbit said to Bear, \"Please pass the honey.\" The bear smiled and shared. Each \"please\" and \"thank you\" made the flowers grow brighter. Kind words were magic.",
            "Behind the old oak tree was a garden no one had seen. Rosa found a rusty key and opened the gate. Inside, flowers sang and butterflies danced. \"You found us!\" sang a rose. \"But the garden only blooms for those who care.\" Rosa watered it every day.",
            "Deep in the hills sat the Wishing Well. Marco wished for a thousand toys. The well glowed and gave him one marble. \"One wish at a time,\" it whispered. Marco played with that marble all day. Sometimes one wish was all you really needed.",
            "Ember the dragon loved to bake cookies, not breathe fire. The other dragons laughed. But when the village oven broke, Ember gently warmed it with her softest flame. The cookies were perfect. \"Being different,\" she smiled, \"is your superpower.\"",
            "Zara found a dusty lamp. When she rubbed it, a tiny genie appeared. \"I grant three wishes!\" Zara thought hard. \"I wish everyone had enough food, enough toys, and enough hugs.\" The genie smiled. \"That's the wisest wish in a thousand years.\"",
            "Far above the clouds lay the Rainbow Kingdom. Every color had a job. Red painted roses, Blue brushed rivers. But Orange felt useless. \"Orange is for sunsets,\" said Yellow. \"And for butterflies,\" added Pink. Orange found its place and painted the most beautiful sunset ever.",
            "A tiny star named Twinkle grew bored of the sky. She fell to earth and landed in a jar. A little girl found her. \"You're beautiful,\" said the girl, and set her free. Twinkle flew back home, glowing brighter than ever. Being wanted was better than being famous."
        ],
        "bedtime": [
            "The moon peeked through the curtains. \"Time for sleep,\" it whispered. Luna yawned and counted the moonbeams on her wall. One, two, three… by the time she reached ten, she was drifting on a soft cloud of dreams.",
            "Beyond the pillow mountain lay Dreamland. Milo sailed there on a blanket boat. Cotton candy clouds floated by. Dreamland had no rules — you could fly, swim through air, or talk to teddy bears. \"See you tomorrow,\" yawned Milo, sailing home to sleep.",
            "Nina counted stars on her ceiling. One for Mama, one for Papa, one for her teddy. But the stars kept multiplying until the ceiling was a sky of twinkling lights. She snuggled deeper into her blanket. The stars would watch over her all night.",
            "Teddy hadn't moved from his spot all day. But at bedtime, Teddy whispered, \"Let's go on an adventure.\" They traveled to the Land of Fluffy Pillows, where everything was soft. Teddy tucked Milo in and said, \"Goodnight, my friend.\"",
            "The night animals woke up as the sun went down. An owl hooted softly. A fox tiptoed. A bat fluttered. \"They're having their own day,\" whispered Mom. \"And we're having ours — time for sweet dreams.\"",
            "Leo built a pillow fort so tall it touched the ceiling. Inside, he had blankets, a flashlight, and his favorite book. \"This is my castle,\" he said. The fort was warm and safe. By the third page, Leo was fast asleep.",
            "A firefly named Glimmer visited every window in town. She checked on sleeping children and left tiny sparkles of light by their beds. When she reached Oliver's room, she saw him smiling in his sleep. \"Sweet dreams,\" she blinked, and flew away.",
            "\"Goodnight moon, goodnight stars, goodnight cars,\" whispered Ava. She said goodnight to her shoes, her mirror, and the tree outside. \"Goodnight, Ava,\" whispered the house. And Ava finally closed her eyes.",
            "Starlight filtered through the window like powdered sugar. Mom sat on the edge of the bed. \"The stars are proud of you today,\" she said. \"You were kind, you shared, and you tried your best. Now rest.\" Those words wrapped around Mateo like a warm hug.",
            "Blanky wasn't just a blanket. It was a cape, a tent, a magic carpet. Max wrapped Blanky around himself and imagined flying over the city. The wind was soft. The stars were bright. Max landed gently in dreamland and slept until morning."
        ]
    }
    pool = stories.get(category, stories["bedtime"])
    i = hash(theme) % len(pool)
    return pool[i]


# ─── GENERATE AUDIO ────────────────────────────────────────────────────

def generate_audio(text, config):
    from gtts import gTTS
    today = datetime.now().strftime("%Y%m%d")
    output_path = AUDIO_DIR / f"story_{today}.mp3"
    tts = gTTS(text=text, lang=config["language"], slow=config["tts"]["slow"])
    tts.save(str(output_path))
    log.info(f"Audio: {output_path}")
    return output_path


# ─── CREATE THUMBNAIL ──────────────────────────────────────────────────

def create_thumbnail(title, category, config):
    from PIL import Image, ImageDraw, ImageFont
    today = datetime.now().strftime("%Y%m%d")
    output_path = THUMB_DIR / f"thumb_{today}.png"

    # Color scheme by category
    colors = {
        "morals": ("#FF6B6B", "#FFE66D"),       # coral + yellow
        "fairy_tales": ("#6C5CE7", "#A29BFE"),  # purple + lavender
        "bedtime": ("#2D3436", "#636E72"),       # dark navy + grey
    }
    color1, color2 = colors.get(category, colors["morals"])

    img = Image.new("RGB", (1280, 720), color1)
    draw = ImageDraw.Draw(img)

    # Gradient
    for i in range(720):
        r = int(int(color1[1:3], 16) + (int(color2[1:3], 16) - int(color1[1:3], 16)) * i / 720)
        g = int(int(color1[3:5], 16) + (int(color2[3:5], 16) - int(color1[3:5], 16)) * i / 720)
        b = int(int(color1[5:7], 16) + (int(color2[5:7], 16) - int(color1[5:7], 16)) * i / 720)
        draw.line([(0, i), (1280, i)], fill=(r, g, b))

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font = font_small = ImageFont.load_default()

    # Emoji indicator by category
    emoji = {"morals": "🌟", "fairy_tales": "🧚", "bedtime": "🌙"}

    title_short = title[:35] + "..." if len(title) > 35 else title
    bbox = draw.textbbox((0, 0), f"{emoji.get(category, '📖')} {title_short}", font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((1280 - text_w) // 2, 280), f"{emoji.get(category, '📖')} {title_short}", fill="white", font=font)
    draw.text((50, 630), "✨ Tiny Tales - Daily Stories", fill="white", font=font_small)
    draw.text((50, 665), f"#kidsstories #{category}", fill="white", font=font_small)

    img.save(str(output_path))
    log.info(f"Thumbnail: {output_path}")
    return output_path


# ─── COMPILE VIDEO ─────────────────────────────────────────────────────

def create_video(audio_path, thumb_path):
    today = datetime.now().strftime("%Y%m%d")
    output_path = VIDEO_DIR / f"video_{today}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(thumb_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]

    subprocess.run(cmd, capture_output=True, text=True, check=True)
    log.info(f"Video: {output_path}")
    return output_path


# ─── UPLOAD TO YOUTUBE ─────────────────────────────────────────────────

def upload_to_youtube(video_path, thumb_path, title, description, config):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
        TOKEN_FILE = BASE / "youtube_token.pickle"
        CREDS_FILE = BASE / "client_secrets.json"

        if not CREDS_FILE.exists():
            log.warning("No client_secrets.json - YouTube upload skipped")
            log.info("Setup: https://console.cloud.google.com/apis/credentials")
            log.info(f"Save as: {CREDS_FILE}")
            return False

        credentials = None
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "rb") as f:
                credentials = pickle.load(f)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
                credentials = flow.run_local_server(port=8080)
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(credentials, f)

        youtube = build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": config["youtube"]["tags"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": config["youtube"]["privacy_status"],
                "selfDeclaredMadeForKids": True
            }
        }

        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response["id"]
        log.info(f"✅ Uploaded! https://youtu.be/{video_id}")

        if thumb_path and thumb_path.exists():
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumb_path))
            ).execute()
            log.info(f"✅ Thumbnail uploaded")

        return video_id
    except Exception as e:
        log.error(f"Upload failed: {e}")
        return False


# ─── GENERATE DASHBOARD ────────────────────────────────────────────────

def generate_dashboard(data, config):
    """Generate a static HTML dashboard with stats."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{config['dashboard']['title']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f23;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 40px 20px;
  }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{
    font-size: 2.2rem;
    margin-bottom: 8px;
    background: linear-gradient(135deg, {config['dashboard']['theme_color']}, #FFE66D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .subtitle {{ color: #888; margin-bottom: 30px; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 30px;
  }}
  .card {{
    background: #1a1a3e;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
  }}
  .card .value {{
    font-size: 2rem;
    font-weight: 700;
    color: {config['dashboard']['theme_color']};
  }}
  .card .label {{ font-size: 0.85rem; color: #888; margin-top: 4px; }}
  .card .icon {{ font-size: 1.5rem; margin-bottom: 8px; }}
  h2 {{ font-size: 1.3rem; margin-bottom: 16px; color: #ccc; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; padding: 10px 12px; color: #888; font-size: 0.8rem; border-bottom: 1px solid #2a2a4e; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1a1a3e; }}
  tr:hover td {{ background: #1a1a3e; }}
  .status-active {{ color: #4ade80; }}
  .status-pending {{ color: #fbbf24; }}
  .footer {{ margin-top: 40px; color: #555; font-size: 0.75rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>{config['dashboard']['title']}</h1>
  <p class="subtitle">📊 Channel Performance Tracker</p>

  <div class="grid">
    <div class="card">
      <div class="icon">🎬</div>
      <div class="value">{data['total_videos']}</div>
      <div class="label">Total Videos</div>
    </div>
    <div class="card">
      <div class="icon">🔥</div>
      <div class="value">{data['current_streak']}</div>
      <div class="label">Day Streak</div>
    </div>
    <div class="card">
      <div class="icon">ℹ️</div>
      <div class="value">-</div>
      <div class="label">Total Views</div>
    </div>
    <div class="card">
      <div class="icon">💰</div>
      <div class="value">$0.00</div>
      <div class="label">Est. Revenue</div>
    </div>
  </div>

  <h2>📅 Upload History</h2>
  <table>
    <tr><th>Date</th><th>Title</th><th>Category</th><th>Status</th></tr>
"""

    if data["videos"]:
        for v in reversed(data["videos"][-20:]):
            status_badge = "✅" if v.get("uploaded") else "📁 Local"
            html += f"<tr><td>{v['date']}</td><td>{v['title'][:30]}...</td><td>{v.get('category','-')}</td><td>{status_badge}</td></tr>"
    else:
        html += '<tr><td colspan="4" style="text-align:center; color:#555;">No videos yet. Run the pipeline to start!</td></tr>'

    html += f"""
  </table>

  <div class="footer">
    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
    Generated by Tiny Tales Automation Pipeline
  </div>
</div>
</body>
</html>"""

    dashboard_path = DASHBOARD_DIR / "index.html"
    dashboard_path.write_text(html)
    log.info(f"Dashboard: {dashboard_path}")
    return dashboard_path


# ─── MAIN ──────────────────────────────────────────────────────────────

def main():
    config = load_config()
    data = load_data()

    log.info(f"🎬 Starting daily video for {config['channel_name']}")

    # Step 1: Generate script
    log.info("📝 Step 1: Writing story...")
    script, category, theme = generate_script(config)
    log.info(f"   [{category}] {script[:60]}...")

    # Create title from first sentence
    first_sentence = script.split(".")[0].strip()
    emoji_map = {"morals": "🌟", "fairy_tales": "🧚", "bedtime": "🌙"}
    title = f"{emoji_map.get(category, '📖')} {first_sentence}"
    description = (
        f"{script}\n\n"
        f"---\n"
        f"✨ Tiny Tales - Daily Stories for Kids\n"
        f"#kidsstories #{category} #storiesforkids #shorts"
    )

    story_file = SCRIPTS_DIR / f"story_{datetime.now().strftime('%Y%m%d')}.txt"
    story_file.write_text(f"[{category}] {theme}\n\n{script}")

    # Step 2: Generate audio
    log.info("🎵 Step 2: Voiceover...")
    audio_path = generate_audio(script, config)

    # Step 3: Create thumbnail
    log.info("🖼️ Step 3: Thumbnail...")
    thumb_path = create_thumbnail(first_sentence, category, config)

    # Step 4: Compile video
    log.info("🎬 Step 4: Compiling video...")
    video_path = create_video(audio_path, thumb_path)

    # Step 5: Upload
    log.info("📤 Step 5: YouTube upload...")
    video_id = upload_to_youtube(video_path, thumb_path, title, description, config)

    # Track
    today_str = date.today().isoformat()
    entry = {
        "date": today_str,
        "title": title,
        "category": category,
        "theme": theme,
        "uploaded": bool(video_id),
        "video_id": video_id or None,
    }
    data["videos"].append(entry)
    data["total_videos"] = len(data["videos"])

    # Streak
    if data["videos"]:
        streak = 1
        for i in range(len(data["videos"]) - 2, -1, -1):
            from datetime import timedelta
            curr = date.fromisoformat(data["videos"][i + 1]["date"])
            prev = date.fromisoformat(data["videos"][i]["date"])
            if (curr - prev).days == 1:
                streak += 1
            else:
                break
        data["current_streak"] = streak

    data["last_upload"] = today_str
    save_data(data)

    # Generate dashboard
    log.info("📊 Step 6: Dashboard...")
    dashboard_path = generate_dashboard(data, config)

    log.info("✅ Done! Video pipeline completed.")
    log.info(f"   Story: [{category}] {first_sentence}")
    log.info(f"   Video: {video_path}")
    log.info(f"   Dashboard: {dashboard_path.name}")
    if video_id:
        log.info(f"   YouTube: https://youtu.be/{video_id}")


if __name__ == "__main__":
    main()
