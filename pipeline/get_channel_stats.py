import os
import sys
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_stats():
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not (client_id and client_secret and refresh_token):
        print("ERROR: Missing YouTube credentials")
        sys.exit(1)

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    if not credentials.valid:
        credentials.refresh(Request())

    youtube = build('youtube', 'v3', credentials=credentials)

    # 2. Extract video IDs from upload_history.log
    video_ids = []
    if os.path.exists('upload_history.log'):
        with open('upload_history.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'ID: ' in line:
                    parts = line.split('ID: ')
                    vid = parts[1].split(' | ')[0].strip()
                    if vid and vid not in video_ids:
                        video_ids.append(vid)

    print(f"Checking stats for {len(video_ids)} uploaded videos...")
    
    # YouTube API accepts up to 50 IDs comma-separated
    v_resp = youtube.videos().list(part='snippet,statistics', id=','.join(video_ids)).execute()
    
    results = []
    for item in v_resp.get('items', []):
        vid_id = item['id']
        snippet = item['snippet']
        stats = item['statistics']
        title = snippet['title']
        published = snippet['publishedAt']
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        
        results.append({
            'id': vid_id,
            'title': title,
            'published': published,
            'views': views,
            'likes': likes,
            'comments': comments,
            'url': f"https://www.youtube.com/shorts/{vid_id}"
        })

    # Sort by views descending
    results.sort(key=lambda x: x['views'], reverse=True)

    print("\n--- VIDEO PERFORMANCE LEADERBOARD (BY VIEWS) ---")
    for rank, r in enumerate(results, 1):
        print(f"#{rank} | Views: {r['views']:6d} | Likes: {r['likes']:4d} | Comments: {r['comments']:3d} | {r['title']} | URL: {r['url']}")

    with open('output_stats.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    get_stats()
