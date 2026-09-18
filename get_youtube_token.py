import os
import json
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("=" * 60)
    print("SciBytes - YouTube OAuth Token Generator")
    print("=" * 60)

    client_secrets_file = "client_secret.json"
    flow = None

    if os.path.exists(client_secrets_file):
        print(f"Found {client_secrets_file}!")
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    else:
        print("Enter your Google Cloud OAuth Client credentials:")
        print("(From Google Cloud Console -> APIs & Services -> Credentials)")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()

        if not client_id or not client_secret:
            print("ERROR: Client ID and Client Secret are required.")
            sys.exit(1)

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\nOpening your browser for one-time YouTube authorization...")
    credentials = flow.run_local_server(port=8080, prompt='consent')

    token_data = {
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri
    }

    with open("token.json", "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)

    print("\n" + "=" * 60)
    print("AUTHORIZATION SUCCESSFUL! Token saved to token.json")
    print("=" * 60)
    print("\nAdd these 3 values to your GitHub Repository Secrets:")
    print("Go to: GitHub Repo -> Settings -> Secrets and variables -> Actions -> New repository secret\n")
    print(f"Secret Name: YOUTUBE_CLIENT_ID")
    print(f"Value:       {credentials.client_id}\n")
    print(f"Secret Name: YOUTUBE_CLIENT_SECRET")
    print(f"Value:       {credentials.client_secret}\n")
    print(f"Secret Name: YOUTUBE_REFRESH_TOKEN")
    print(f"Value:       {credentials.refresh_token}\n")
    print("=" * 60)

if __name__ == '__main__':
    main()
