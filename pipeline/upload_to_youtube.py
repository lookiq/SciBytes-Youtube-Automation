import os
import sys
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

METADATA_FILE = 'output/metadata.json'
VIDEO_FILE = 'output/scibytes_short_latest.mp4'
DATABASE_FILE = 'pipeline/topics_database.json'

def load_env_file():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k] = v

def get_authenticated_service():
    load_env_file()
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not (client_id and client_secret and refresh_token):
        print("ERROR: Missing YouTube OAuth credentials in environment variables or .env file.")
        print("Please ensure YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN are set.")
        sys.exit(1)

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    if not credentials.valid:
        print("Refreshing YouTube access token...")
        credentials.refresh(Request())

    return build('youtube', 'v3', credentials=credentials)

def mark_topic_used(topic_id):
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        for t in topics:
            if t['id'] == topic_id:
                t['used'] = True
                break
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, indent=2)

def upload_video():
    if not os.path.exists(METADATA_FILE):
        print("ERROR: Metadata file not found. Run build_short.py first.")
        sys.exit(1)

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Use SEO offline keyword video file if present, else fallback
    seo_video_name = metadata.get('offline_video_name')
    seo_video_path = os.path.join('output', seo_video_name) if seo_video_name else None
    if seo_video_path and os.path.exists(seo_video_path):
        video_to_upload = seo_video_path
        print(f"Using offline SEO video file: {video_to_upload}")
    elif os.path.exists(VIDEO_FILE):
        video_to_upload = VIDEO_FILE
    else:
        print("ERROR: No video file found to upload. Run build_short.py first.")
        sys.exit(1)

    load_env_file()
    privacy_status = os.environ.get('YOUTUBE_PRIVACY_STATUS', 'public')

    youtube = get_authenticated_service()

    # Sanitize tags to strictly ensure <= 400 YouTube character cost (accounting for quotes and commas)
    raw_tags = metadata.get('tags', [])
    safe_tags = []
    total_cost = 0
    for t in raw_tags:
        cost = len(t) + (2 if ' ' in t else 0) + 1
        if total_cost + cost <= 400:
            safe_tags.append(t)
            total_cost += cost

    body = {
        'snippet': {
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': safe_tags,
            'categoryId': metadata.get('category_id', '28'),
            'defaultLanguage': metadata.get('default_language', 'en'),
            'defaultAudioLanguage': metadata.get('default_audio_language', 'en')
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False,
            'license': metadata.get('license', 'youtube'),
            'embeddable': True
        }
    }

    print(f"Uploading '{metadata['title']}' to YouTube (SEO Mode: 100% VidIQ Optimized)...")
    media = MediaFileUpload(video_to_upload, mimetype='video/mp4', resumable=True)

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
    except Exception as e:
        if 'invalidTags' in str(e):
            print("WARNING: Encountered invalidTags from YouTube API. Retrying with essential core tags...")
            body['snippet']['tags'] = ['science facts', 'space facts', 'astronomy', 'physics', 'shorts']
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=MediaFileUpload(video_to_upload, mimetype='video/mp4', resumable=True)
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")
        else:
            raise e

    video_id = response.get('id')
    video_url = f"https://www.youtube.com/shorts/{video_id}"
    print("=" * 60)
    print("SUCCESS: Video uploaded successfully to YouTube!")
    print(f"Shorts URL: {video_url}")
    print("=" * 60)

    # Set high-CTR custom thumbnail (use offline SEO thumbnail if available)
    seo_thumb_name = metadata.get('offline_thumb_name')
    seo_thumb_path = os.path.join('output', seo_thumb_name) if seo_thumb_name else None
    if seo_thumb_path and os.path.exists(seo_thumb_path):
        thumbnail_file = seo_thumb_path
    else:
        thumbnail_file = 'output/thumbnail.jpg'

    if os.path.exists(thumbnail_file):
        try:
            print(f"Setting high-CTR custom thumbnail via YouTube API: {thumbnail_file}...")
            thumb_media = MediaFileUpload(thumbnail_file, mimetype='image/jpeg')
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=thumb_media
            ).execute()
            print("Custom thumbnail successfully attached!")
        except Exception as e:
            print(f"Notice on custom thumbnail API: {e}")

    mark_topic_used(metadata.get('id'))

    log_entry = f"[{datetime.now().isoformat()}] ID: {video_id} | Title: {metadata['title']} | Footage: {metadata.get('footage_url', 'N/A')} | URL: {video_url}\n"
    with open('upload_history.log', 'a', encoding='utf-8') as f:
        f.write(log_entry)

    return video_url

if __name__ == '__main__':
    upload_video()
