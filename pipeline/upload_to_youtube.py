import os
import sys
import json
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_FILE = os.path.join(BASE_DIR, 'output', 'metadata.json')
TOPICS_FILE = os.path.join(BASE_DIR, 'pipeline', 'topics_database.json')

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    token_file = os.path.join(BASE_DIR, 'token.json')
    if os.path.exists(token_file):
        print(f"Loading credentials from local file: {token_file}")
        with open(token_file, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
            client_id = token_data.get('client_id', client_id)
            client_secret = token_data.get('client_secret', client_secret)
            refresh_token = token_data.get('refresh_token', refresh_token)

    if not client_id or not client_secret or not refresh_token:
        print("ERROR: Missing YouTube credentials.")
        print("Required environment variables or secrets: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        print("Run 'python get_youtube_token.py' to generate your credentials.")
        sys.exit(1)

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    return build('youtube', 'v3', credentials=credentials)

def upload_video():
    if not os.path.exists(METADATA_FILE):
        print(f"ERROR: Metadata file not found at: {METADATA_FILE}")
        sys.exit(1)

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    video_path = meta['video_file']
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found at: {video_path}")
        sys.exit(1)

    youtube = get_authenticated_service()

    privacy = os.environ.get('YOUTUBE_PRIVACY_STATUS', 'public')

    body = {
        'snippet': {
            'title': meta['title'],
            'description': meta['description'],
            'tags': meta.get('tags', []),
            'categoryId': '28' # Science & Technology
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False
        }
    }

    print(f"Starting upload for: {meta['title']}")
    print(f"Privacy status: {privacy}")
    print(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")

    media = MediaFileUpload(video_path, mimetype='video/mp4', chunksize=1024*1024*4, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%...")

    video_id = response.get('id')
    print(f"SUCCESS! Video uploaded.")
    print(f"Video ID: {video_id}")
    print(f"Watch URL: https://youtube.com/shorts/{video_id}")

    # Mark topic as used
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        for t in topics:
            if t.get('id') == meta.get('id'):
                t['used'] = True
                break
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, indent=2)
        print("Updated topics_database.json (marked topic as used).")

    return video_id

if __name__ == '__main__':
    upload_video()
