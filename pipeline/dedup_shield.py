import os
import sys
import json
import re
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

DATABASE_FILE = os.path.join(PROJECT_ROOT, 'pipeline', 'topics_database.json')
UPLOAD_HISTORY_FILE = os.path.join(PROJECT_ROOT, 'upload_history.log')
USED_CLIPS_FILE = os.path.join(SCRIPT_DIR, 'assets', 'used_clips_registry.json')
USED_TOPICS_FILE = os.path.join(SCRIPT_DIR, 'assets', 'used_topics_registry.json')

def normalize_title(title):
    if not title:
        return ""
    clean = re.sub(r'#\w+', '', title)
    clean = re.sub(r'[-–—:!?.,\'"()\[\]]', ' ', clean)
    clean = ' '.join(clean.lower().split())
    return clean

def extract_asset_key(url_or_path):
    if not url_or_path or url_or_path in ['N/A', 'None', '']:
        return None
    raw = urllib.parse.unquote(str(url_or_path).strip())
    # 1. Match NASA video asset directory/identifier
    match = re.search(r'/video/([^/~]+)', raw, re.IGNORECASE)
    if match:
        return 'nasa:' + match.group(1).strip().lower()
    # 2. Match local file or direct URL base name
    base = raw.split('?')[0].split('#')[0].rstrip('/').split('/')[-1].split('\\')[-1]
    base = re.sub(r'~(orig|large|medium|small|1080p|720p)', '', base, flags=re.I)
    base = re.sub(r'\.(mp4|mov|webm|mkv|jpg|png)$', '', base, flags=re.I)
    return 'file:' + base.strip().lower()

def load_used_footages():
    used_urls = set()
    used_keys = set()

    # Source 1: upload_history.log
    if os.path.exists(UPLOAD_HISTORY_FILE):
        try:
            with open(UPLOAD_HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Footage: ' in line:
                        parts = line.split('Footage: ')
                        if len(parts) > 1:
                            f_url = parts[1].split(' | ')[0].strip()
                            if f_url and f_url != 'N/A':
                                used_urls.add(f_url)
                                key = extract_asset_key(f_url)
                                if key:
                                    used_keys.add(key)
        except Exception as e:
            print(f"Warning reading upload_history.log: {e}")

    # Source 2: topics_database.json (all marked used)
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                topics = json.load(f)
            for t in topics:
                if t.get('used', False):
                    f_url = t.get('footage_url')
                    if f_url:
                        used_urls.add(f_url)
                        key = extract_asset_key(f_url)
                        if key:
                            used_keys.add(key)
        except Exception as e:
            print(f"Warning reading topics_database.json: {e}")

    # Source 3: used_clips_registry.json
    if os.path.exists(USED_CLIPS_FILE):
        try:
            with open(USED_CLIPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for u in data.get('urls', []):
                    used_urls.add(u)
                for k in data.get('asset_keys', []):
                    used_keys.add(k)
        except Exception:
            pass

    return used_urls, used_keys

def load_used_topics():
    used_ids = set()
    used_titles = set()

    # Source 1: upload_history.log
    if os.path.exists(UPLOAD_HISTORY_FILE):
        try:
            with open(UPLOAD_HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Title: ' in line:
                        parts = line.split('Title: ')
                        if len(parts) > 1:
                            raw_title = parts[1].split(' | ')[0].strip()
                            norm = normalize_title(raw_title)
                            if norm:
                                used_titles.add(norm)
        except Exception as e:
            print(f"Warning reading upload_history.log: {e}")

    # Source 2: topics_database.json
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                topics = json.load(f)
            for t in topics:
                if t.get('used', False):
                    if t.get('id'):
                        used_ids.add(t.get('id').strip().lower())
                    norm = normalize_title(t.get('title', ''))
                    if norm:
                        used_titles.add(norm)
        except Exception as e:
            print(f"Warning reading topics_database.json: {e}")

    # Source 3: used_topics_registry.json
    if os.path.exists(USED_TOPICS_FILE):
        try:
            with open(USED_TOPICS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for tid in data.get('ids', []):
                    used_ids.add(tid.strip().lower())
                for ttitle in data.get('titles', []):
                    used_titles.add(ttitle)
        except Exception:
            pass

    return used_ids, used_titles

def is_clip_already_used(clip_url_or_path):
    if not clip_url_or_path or clip_url_or_path in ['N/A', 'None']:
        return False
    used_urls, used_keys = load_used_footages()
    raw = str(clip_url_or_path).strip()
    if raw in used_urls:
        return True
    key = extract_asset_key(raw)
    if key and key in used_keys:
        return True
    return False

def is_topic_already_used(topic_id, title=None):
    used_ids, used_titles = load_used_topics()
    if topic_id and topic_id.strip().lower() in used_ids:
        return True
    if title:
        norm = normalize_title(title)
        if norm and norm in used_titles:
            return True
        # Check partial overlap with past titles (core 5 words)
        words = norm.split()
        if len(words) >= 4:
            core = ' '.join(words[:4])
            for ut in used_titles:
                if core in ut:
                    return True
    return False

def record_content_upload(topic_id, title, footage_urls=None, youtube_id=None):
    """
    Permanently records an uploaded video, topic, and all associated footage clips
    into the persistent anti-reuse registries.
    """
    os.makedirs(os.path.dirname(USED_CLIPS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(USED_TOPICS_FILE), exist_ok=True)

    # 1. Update Topics Registry
    used_ids, used_titles = load_used_topics()
    if topic_id:
        used_ids.add(topic_id.strip().lower())
    if title:
        norm = normalize_title(title)
        if norm:
            used_titles.add(norm)

    with open(USED_TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'ids': sorted(list(used_ids)), 'titles': sorted(list(used_titles))}, f, indent=2)

    # 2. Update Clips Registry
    used_urls, used_keys = load_used_footages()
    if footage_urls:
        if isinstance(footage_urls, str):
            footage_urls = [footage_urls]
        for f_url in footage_urls:
            if f_url and f_url != 'N/A':
                used_urls.add(str(f_url).strip())
                key = extract_asset_key(f_url)
                if key:
                    used_keys.add(key)

    with open(USED_CLIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'urls': sorted(list(used_urls)), 'asset_keys': sorted(list(used_keys))}, f, indent=2)

    # 3. Mark used in topics_database.json if present
    if os.path.exists(DATABASE_FILE) and topic_id:
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                topics = json.load(f)
            changed = False
            for t in topics:
                if t.get('id') == topic_id or normalize_title(t.get('title', '')) == normalize_title(title):
                    t['used'] = True
                    changed = True
            if changed:
                with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(topics, f, indent=2)
        except Exception as e:
            print(f"Warning syncing database topic status: {e}")

    print(f"[DEDUP SHIELD] Permanently recorded topic '{title}' and clips in anti-reuse shield.")

def get_fresh_nasa_clip(search_query):
    """
    Dynamically queries NASA's library of 100,000+ open-source space clips
    and returns a guaranteed NEVER-USED footage URL.
    """
    clean_kw = search_query.replace('#', '').strip()
    url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(clean_kw)}&media_type=video"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    used_urls, used_keys = load_used_footages()

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('collection', {}).get('items', [])
            for it in items[:15]:
                d = it['data'][0]
                nid = d.get('nasa_id')
                title = d.get('title', '')
                desc = d.get('description', '')
                lower_check = (title + " " + desc).lower()
                if any(bad in lower_check for bad in ['interview', 'briefing', 'press conference', 'talks', 'speaking', 'panel', 'town hall']):
                    continue
                asset_url = f"https://images-api.nasa.gov/asset/{nid}"
                req2 = urllib.request.Request(asset_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req2, timeout=10) as r2:
                    c2 = json.loads(r2.read().decode('utf-8'))
                    mp4s = [x['href'] for x in c2.get('collection', {}).get('items', []) if x['href'].endswith('.mp4')]
                    orig = [x for x in mp4s if '~orig.mp4' in x or '~large.mp4' in x or '~1080p.mp4' in x]
                    candidate = orig[0] if orig else (mp4s[0] if mp4s else None)
                    if candidate:
                        cand_key = extract_asset_key(candidate)
                        if candidate not in used_urls and (not cand_key or cand_key not in used_keys):
                            print(f"[DEDUP SHIELD] Found fresh, never-used NASA footage: '{title}' ({candidate})")
                            return candidate
    except Exception as e:
        print(f"Notice querying NASA API for fresh footage: {e}")
    return None

if __name__ == '__main__':
    u_urls, u_keys = load_used_footages()
    u_ids, u_titles = load_used_topics()
    print("=" * 60)
    print("SCIBYTES UNIVERSAL ANTI-DUPLICATE & ANTI-REUSE SHIELD")
    print("=" * 60)
    print(f"Total Unique Clips/Footages Locked: {len(u_keys)} asset keys ({len(u_urls)} URLs)")
    print(f"Total Unique Topics/Titles Locked:  {len(u_ids)} IDs ({len(u_titles)} Titles)")
    print("=" * 60)
