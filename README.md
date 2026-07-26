# 🎬 Tiny Tales - YouTube Automation

Daily kids' stories channel powered by free tools. Fully automated.

## How it works

1. **Writes** a short children's story (Gemini API or built-in collection)
2. **Records** voiceover via Google TTS (free)
3. **Creates** a colorful thumbnail
4. **Compiles** a 1080x1920 YouTube Shorts video via FFmpeg
5. **(Optional) Uploads** to YouTube via the Data API
6. **Tracks** everything in a live dashboard

## Setup

### 1. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/tiny-tales.git
git push -u origin main
```

### 2. Set up Gemini API (free)
1. Go to https://aistudio.google.com/apikey
2. Get a free API key
3. Add it to GitHub repo secrets as `GEMINI_API_KEY`

### 3. Set up YouTube upload (free)
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Desktop app)
3. Download `client_secrets.json` and place it in the project root
4. Run locally once to authorize: `python run.py`

### 4. Enable GitHub Pages for dashboard
1. Go to repo Settings > Pages
2. Source: Deploy from branch > `main` > `/dashboard`
3. Your dashboard will be at `https://YOUR_USERNAME.github.io/tiny-tales/`

## Run locally
```bash
pip install -r requirements.txt
python run.py
```

## Customize
Edit `config.yaml` to change the channel name, story themes, or upload schedule.

## Tech stack (all free)
- Python 3
- Google Gemini API (free tier)
- gTTS (free text-to-speech)
- Pillow (thumbnail generation)
- FFmpeg (video compilation)
- YouTube Data API (free quota)
- GitHub Actions (free CI/CD)
