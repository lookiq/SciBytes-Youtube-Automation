# SciBytes - 24/7 Cloud Automated YouTube Shorts Pipeline

Automated YouTube Shorts channel pipeline for **SciBytes** (`@SciBytesDaily`).
Runs completely in the cloud via **GitHub Actions** on a daily schedule—**even when your computer is powered off**.

---

## Features
- **Zero Cost:** Runs on GitHub Actions free runner (2,000 free minutes/month).
- **Automated Research & Script:** Curated viral science/space/physics topics with high-retention hooks.
- **Natural Voice:** Microsoft Edge-TTS Christopher Neural voice (100% free, natural tone).
- **Authentic B-Roll:** Real NASA and public domain 1080p science footage.
- **Dynamic Subtitles:** Scienceverse-style colored text boxes and vertical 1080x1920 layout.
- **Cloud YouTube Upload:** Uploads directly to YouTube Studio with SEO-optimized titles, descriptions, and tags.

---

## Daily Schedule
- **Cron:** `30 14 * * *`
- **Time:** 14:30 UTC
  - **USA Eastern Time (EST):** 10:30 AM (Seeds right into USA 12:00 PM lunch-break peak!)
  - **Bangladesh Time (BST):** 8:30 PM

---

## Setup Instructions

### 1. One-Time YouTube API Token Generation
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create an OAuth 2.0 Client ID (Desktop Application).
3. Run the helper script on your PC:
   ```bash
   python get_youtube_token.py
   ```
4. Sign in with your YouTube Google account and grant upload permissions.
5. The script will display your `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`.

### 2. Add Secrets to GitHub
1. In your GitHub repository, go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add:
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`

### 3. Trigger Manually Anytime
1. In GitHub, go to the **Actions** tab.
2. Select **Daily SciBytes Short Automation**.
3. Click **Run workflow** -> **Run workflow**.
