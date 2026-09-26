import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

HISTORY_FILE = os.path.join(SCRIPT_DIR, 'assets', 'processed_viral_history.json')

SEARCH_QUERIES = [
    'space facts shorts',
    'black hole mystery shorts',
    'universe what if shorts',
    'astronomy mind blowing shorts',
    'nasa james webb discoveries shorts',
    'quantum physics facts shorts'
]

HIGH_SEARCH_KEYWORDS = [
    'black hole', 'james webb', 'solar storm', 'sun', 'quantum',
    'time dilation', 'speed of light', 'supernova', 'neutron star',
    'voyager', 'event horizon', 'oumuamua', 'jupiter', 'mars', 'relativity'
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(processed_set):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(processed_set), f, indent=2)

def parse_views_str(v_str):
    v = v_str.lower().replace('views', '').strip()
    if 'm' in v:
        return float(v.replace('m', '').strip()) * 1_000_000
    elif 'k' in v:
        return float(v.replace('k', '').strip()) * 1_000
    try:
        return float(re.sub(r'[^0-9.]', '', v))
    except Exception:
        return 0

def discover_top_viral_shorts(limit=5):
    print("=" * 60)
    print("SCIBYTES AUTONOMOUS VIRAL TREND HUNTER")
    print("Searching YouTube & social algorithms for top space shorts...")
    print("=" * 60)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    history = load_history()
    all_candidates = {}

    for q in SEARCH_QUERIES:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}"
        req = urllib.request.Request(url, headers=headers)
        try:
            html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')
            m = re.search(r'var ytInitialData = ({.*?});</script>', html)
            if not m:
                continue
            data = json.loads(m.group(1))

            def extract_shorts(d):
                if isinstance(d, dict):
                    if 'shortsLockupViewModel' in d:
                        vm = d['shortsLockupViewModel']
                        ent = vm.get('entityId', '')
                        vid_id = ent.replace('shorts-shelf-item-', '')
                        meta = vm.get('overlayMetadata', {})
                        title = meta.get('primaryText', {}).get('content', '')
                        views_str = meta.get('secondaryText', {}).get('content', '0')
                        if vid_id and title and vid_id not in history:
                            approx_views = parse_views_str(views_str)
                            clean_t = title.encode('ascii', 'ignore').decode().strip()
                            all_candidates[vid_id] = {
                                'id': vid_id,
                                'url': f'https://www.youtube.com/shorts/{vid_id}',
                                'title': clean_t,
                                'views_str': views_str,
                                'approx_views': approx_views
                            }
                    for v in d.values():
                        extract_shorts(v)
                elif isinstance(d, list):
                    for item in d:
                        extract_shorts(item)

            extract_shorts(data)
        except Exception as e:
            print(f"Notice during query '{q}': {e}")

    print(f"Discovered {len(all_candidates)} unique un-replicated Shorts.")
    if not all_candidates:
        print("No new shorts found; resetting history filter.")
        history.clear()
        save_history(history)
        return []

    # Sort initially by approximate views
    sorted_by_views = sorted(all_candidates.values(), key=lambda x: x['approx_views'], reverse=True)
    sample_pool = sorted_by_views[:12]

    print("\nCalculating exact Views Per Hour (VPH) and engagement scores...")
    ranked = []
    now = time.time()

    for s in sample_pool:
        cmd = ['yt-dlp', s['url'], '--dump-json', '--skip-download']
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        if res.returncode == 0:
            try:
                d = json.loads(res.stdout)
                exact_views = d.get('view_count', s['approx_views'])
                likes = d.get('like_count', 0)
                duration = d.get('duration', 30)
                upload_ts = d.get('timestamp')
                uploader = d.get('uploader', 'Unknown')
                full_title = d.get('title', s['title'])

                if duration and (duration < 8 or duration > 65):
                    continue

                if upload_ts:
                    hours = max(1.0, (now - upload_ts) / 3600.0)
                    vph = exact_views / hours
                else:
                    hours = 24.0
                    vph = exact_views / 24.0

                eng_ratio = (likes / max(1, exact_views)) * 100 if likes else 4.0

                # Keyword demand boost (VidIQ criteria)
                kw_boost = sum(1 for kw in HIGH_SEARCH_KEYWORDS if kw in full_title.lower())

                score = (vph * 0.5) + (exact_views * 0.05) + (eng_ratio * 80) + (kw_boost * 500)

                ranked.append({
                    'id': s['id'],
                    'url': s['url'],
                    'title': full_title,
                    'uploader': uploader,
                    'views': exact_views,
                    'likes': likes,
                    'duration': duration,
                    'hours_live': hours,
                    'vph': vph,
                    'eng_ratio': eng_ratio,
                    'viral_score': score
                })
            except Exception:
                pass

    ranked.sort(key=lambda x: x['viral_score'], reverse=True)

    print("\n" + "=" * 60)
    print("TOP VIRAL CANDIDATES RANKED BY VPH & ENGAGEMENT:")
    print("=" * 60)
    for i, r in enumerate(ranked[:limit], 1):
        clean_title = r['title'].encode('ascii', 'ignore').decode().strip()
        print(f"\n#{i} VIRAL CANDIDATE:")
        print(f"Title: {clean_title}")
        print(f"Channel: {r['uploader']}")
        print(f"Total Views: {r['views']:,} | VPH: {r['vph']:.1f} views/hour | Duration: {r['duration']}s")
        print(f"URL: {r['url']}")

    return ranked[:limit]

def auto_hunt_and_build(upload=False):
    candidates = discover_top_viral_shorts(limit=5)
    if not candidates:
        print("ERROR: Could not discover any new viral candidates. Please try again.")
        sys.exit(1)

    winner = candidates[0]
    clean_winner_title = winner['title'].encode('ascii', 'ignore').decode().strip()
    print("\n" + "=" * 60)
    print(f"SELECTED #1 VIRAL SHORT TO RE-ENGINEER:")
    print(f"Title: {clean_winner_title}")
    print(f"VPH: {winner['vph']:.1f} views/hour | Views: {winner['views']:,}")
    print(f"URL: {winner['url']}")
    print("=" * 60 + "\n")

    # Import and run viral processor
    from pipeline.build_from_viral import process_viral_short
    process_viral_short(winner['url'], upload=upload)

    # Record in history so we never duplicate
    history = load_history()
    history.add(winner['id'])
    save_history(history)
    print(f"\nSaved '{winner['id']}' to viral history. Video generation complete!")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Viral Space Shorts Hunter")
    parser.add_argument('--hunt', action='store_true', help="Only search and rank top viral candidates without building")
    parser.add_argument('--auto', action='store_true', help="Automatically pick #1 viral Short and build for PC preview")
    parser.add_argument('--auto-upload', action='store_true', help="Automatically pick #1 viral Short, build, and upload to YouTube")
    args = parser.parse_args()

    if args.auto_upload:
        auto_hunt_and_build(upload=True)
    elif args.auto:
        auto_hunt_and_build(upload=False)
    else:
        discover_top_viral_shorts(limit=5)
