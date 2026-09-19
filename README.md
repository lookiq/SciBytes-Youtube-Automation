# SciBytes - 24/7 Automated YouTube Shorts Cloud Pipeline

Autonomous daily YouTube Shorts video generation and uploading system for **SciBytes** (`@SciBytesDaily`), designed to run completely in the cloud on **GitHub Actions** even when your local PC is turned off.

---

## 1. Pipeline Architecture

- **Execution Schedule:** Daily at `21:30 UTC` (4:30 PM US Eastern / 5:30 PM US EDT / 3:30 AM Bangladesh BST) to capture the massive **US Evening Prime Time** peak audience.
- **Workflow Engine:** GitHub Actions (Ubuntu 24.04 runner, 100% Free).
- **Voiceover Synthesis:** Microsoft Neural Voice (`en-US-ChristopherNeural` via `edge-tts`).
- **Footage Sourcing:** NASA Public Domain and Science Archives (1080p B-roll).
- **Video Rendering:** High-performance FFmpeg 9:16 vertical broadcast layout with dynamic Scienceverse-style colored subtitles.
- **YouTube Publishing:** Direct upload via YouTube Data API v3 with automatic access token refreshing and category `28` (Science & Technology).

---

## 2. One-Time Setup Instructions

### Step 1: Create a Private GitHub Repository
1. Go to [GitHub.com](https://github.com) and create a new **Private** repository (e.g., `scibytes-automation`).
2. In your local terminal, push this project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: SciBytes automated pipeline"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/scibytes-automation.git
   git push -u origin main
   ```

### Step 2: Get Google Cloud YouTube OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Enable **YouTube Data API v3**.
3. Go to **APIs & Services > Credentials** > **Create Credentials** > **OAuth client ID**.
   - Application type: **Desktop app**.
   - Download JSON or copy the **Client ID** and **Client Secret**.
4. Run our helper script locally on your PC:
   ```bash
   python get_youtube_token.py
   ```
   This will open your browser to authorize your YouTube account once and print your **Refresh Token**.

### Step 3: Add GitHub Secrets
In your GitHub repository:
1. Go to **Settings > Secrets and variables > Actions**.
2. Click **New repository secret** and add:
   - `YOUTUBE_CLIENT_ID`: Your Google OAuth Client ID
   - `YOUTUBE_CLIENT_SECRET`: Your Google OAuth Client Secret
   - `YOUTUBE_REFRESH_TOKEN`: The Refresh Token generated in Step 2

---

## 3. Testing

### Run Locally on Windows:
```bash
python run_pipeline_locally.py
```
This will generate the next short from `topics_database.json`, render the complete video in `output/scibytes_short_latest.mp4`, and open it in Windows Explorer.

### Run on GitHub Actions (Cloud):
1. In your GitHub repository, go to the **Actions** tab.
2. Select **Daily SciBytes Shorts Generator & Uploader**.
3. Click **Run workflow** to test cloud rendering and YouTube upload anytime with 1 click!
