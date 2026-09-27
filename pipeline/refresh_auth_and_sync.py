import os
import sys
import base64
import json
import urllib.request
from google_auth_oauthlib.flow import InstalledAppFlow
from nacl import public

GH_TOKEN = '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'
REPO = 'lookiq/SciBytes-Youtube-Automation'
HEADERS = {
    'Authorization': f'token {GH_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'SciBytes'
}
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def set_github_secret(secret_name: str, secret_value: str):
    url_pk = f'https://api.github.com/repos/{REPO}/actions/secrets/public-key'
    req_pk = urllib.request.Request(url_pk, headers=HEADERS)
    with urllib.request.urlopen(req_pk) as resp:
        pk_data = json.loads(resp.read().decode('utf-8'))
    
    key_id = pk_data['key_id']
    key_b64 = pk_data['key']

    public_key_bytes = base64.b64decode(key_b64)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    encrypted_val = base64.b64encode(encrypted).decode('utf-8')

    payload = json.dumps({
        'encrypted_value': encrypted_val,
        'key_id': key_id
    }).encode('utf-8')

    url_sec = f'https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}'
    req_sec = urllib.request.Request(url_sec, data=payload, headers=HEADERS, method='PUT')
    with urllib.request.urlopen(req_sec) as resp:
        print(f"Successfully synchronized secret '{secret_name}' to GitHub Actions! (HTTP {resp.status})")

def main():
    print("=" * 60)
    print("SciBytes - YouTube OAuth Re-authentication & Auto-Sync")
    print("=" * 60)
    
    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found!")
        sys.exit(1)

    print("\nOpening your default browser for authorization...")
    print("Please select your Google account and click Allow.")
    
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    credentials = flow.run_local_server(port=8088, prompt='consent', access_type='offline', open_browser=True)

    refresh_token = credentials.refresh_token
    client_id = credentials.client_id
    client_secret = credentials.client_secret

    print("\nSUCCESS! New Google Refresh Token obtained.")
    
    # 1. Update local .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"YOUTUBE_CLIENT_ID={client_id}\n")
        f.write(f"YOUTUBE_CLIENT_SECRET={client_secret}\n")
        f.write(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")
        f.write("YOUTUBE_PRIVACY_STATUS=public\n")
        f.write("ELEVENLABS_API_KEY=sk_3bf2a67c20e410d3afeb816417231e119eb1095c364d954c\n")
        f.write("ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB\n")
    print("Updated local .env file.")

    # 2. Sync to GitHub Actions Secrets
    print("Syncing new token to GitHub Actions repository secrets...")
    set_github_secret("YOUTUBE_REFRESH_TOKEN", refresh_token)
    print("=" * 60)
    print("ALL DONE! GitHub Actions automation is now 100% restored!")
    print("=" * 60)

if __name__ == "__main__":
    main()
