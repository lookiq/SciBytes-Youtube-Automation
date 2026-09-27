import os
import sys
import base64
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
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
        print(f"Successfully synchronized secret '{secret_name}' to GitHub Actions! (HTTP {resp.status})", flush=True)

auth_response_query = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_response_query
        auth_response_query = self.path
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """
        <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #121212; color: #fff;">
            <h1 style="color: #4CAF50;">Authentication Successful!</h1>
            <p style="font-size: 18px;">Your new Google YouTube Refresh Token has been acquired.</p>
            <p>You can close this tab now and return to your terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        pass

def main():
    print("=" * 60, flush=True)
    print("SciBytes - YouTube OAuth Re-authentication & Auto-Sync", flush=True)
    print("=" * 60, flush=True)
    
    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found!", flush=True)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    flow.redirect_uri = 'http://localhost:8088/'

    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

    os.makedirs('temp', exist_ok=True)
    with open('temp/auth_link.txt', 'w', encoding='utf-8') as f:
        f.write(auth_url)

    print(f"\n============================================================\nAUTHORIZATION URL:\n{auth_url}\n============================================================\n", flush=True)

    try:
        os.system(f'start "" "{auth_url}"')
    except Exception:
        pass

    server = HTTPServer(('127.0.0.1', 8088), OAuthCallbackHandler)
    print("Waiting for Google authorization callback on http://localhost:8088/...", flush=True)
    
    while auth_response_query is None:
        server.handle_request()

    server.server_close()
    print("Callback received! Exchanging code for refresh token...", flush=True)

    auth_response_full = f"https://localhost:8088{auth_response_query}"
    flow.fetch_token(authorization_response=auth_response_full)

    credentials = flow.credentials
    refresh_token = credentials.refresh_token
    client_id = credentials.client_id
    client_secret = credentials.client_secret

    print("\nSUCCESS! New Google Refresh Token obtained.", flush=True)
    print(f"YOUTUBE_CLIENT_ID: {client_id}", flush=True)
    print(f"YOUTUBE_REFRESH_TOKEN: {refresh_token[:15]}...", flush=True)
    
    # 1. Update local .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"YOUTUBE_CLIENT_ID={client_id}\n")
        f.write(f"YOUTUBE_CLIENT_SECRET={client_secret}\n")
        f.write(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")
        f.write("YOUTUBE_PRIVACY_STATUS=public\n")
        f.write("ELEVENLABS_API_KEY=sk_3bf2a67c20e410d3afeb816417231e119eb1095c364d954c\n")
        f.write("ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB\n")
    print("Updated local .env file.", flush=True)

    # 2. Sync to GitHub Actions Secrets
    print("Syncing new token to GitHub Actions repository secrets...", flush=True)
    set_github_secret("YOUTUBE_REFRESH_TOKEN", refresh_token)
    print("=" * 60, flush=True)
    print("ALL DONE! YouTube automation is now 100% restored!", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    main()
