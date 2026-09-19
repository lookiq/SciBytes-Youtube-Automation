import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("=" * 60, flush=True)
    print("SciBytes - 1-Time YouTube OAuth Setup Helper", flush=True)
    print("=" * 60, flush=True)

    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found!", flush=True)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)

    print("\nOpening your default browser for authorization...", flush=True)
    print("Please select your Google account and click Allow.", flush=True)

    credentials = flow.run_local_server(port=8088, prompt='consent', access_type='offline', open_browser=True)

    refresh_token = credentials.refresh_token
    client_id = credentials.client_id
    client_secret = credentials.client_secret

    print("\n" + "=" * 60, flush=True)
    print("SUCCESS! Refresh Token Generated Successfully!", flush=True)
    print("=" * 60, flush=True)
    print(f"YOUTUBE_CLIENT_ID     : {client_id}", flush=True)
    print(f"YOUTUBE_CLIENT_SECRET : {client_secret}", flush=True)
    print(f"YOUTUBE_REFRESH_TOKEN : {refresh_token}", flush=True)
    print("=" * 60, flush=True)

    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"YOUTUBE_CLIENT_ID={client_id}\n")
        f.write(f"YOUTUBE_CLIENT_SECRET={client_secret}\n")
        f.write(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")
        f.write("YOUTUBE_PRIVACY_STATUS=public\n")
    print("Saved credentials to local .env file.", flush=True)

if __name__ == "__main__":
    main()
