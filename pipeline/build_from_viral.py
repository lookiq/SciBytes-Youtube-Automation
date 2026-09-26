import os
import sys

# Ensure project root and pipeline dir are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse
import json
import urllib.parse
import requests

try:
    from pipeline.transcript_engine import extract_transcript_from_url
    from pipeline.script_reengineer import reengineer_script
    from pipeline.build_short import build_short_pipeline
    from pipeline.seo_engine import generate_seo_metadata
except ImportError:
    from transcript_engine import extract_transcript_from_url
    from script_reengineer import reengineer_script
    from build_short import build_short_pipeline
    from seo_engine import generate_seo_metadata

def search_matching_nasa_footage(keywords):
    query = " ".join(keywords[:2])
    print(f"Searching NASA media archive for 4K/HD footage matching '{query}'...")
    url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=video"
    try:
        res = requests.get(url, timeout=15).json()
        items = res.get('collection', {}).get('items', [])
        for item in items[:5]:
            nasa_id = item.get('data', [{}])[0].get('nasa_id')
            if not nasa_id:
                continue
            col_url = f"https://images-api.nasa.gov/asset/{nasa_id}"
            col_res = requests.get(col_url, timeout=15).json()
            video_files = [x.get('href') for x in col_res.get('collection', {}).get('items', []) if x.get('href', '').endswith('.mp4')]
            # Prefer orig or large
            for f in video_files:
                if '~orig.mp4' in f or '~large.mp4' in f or '~medium.mp4' in f:
                    print(f"Matched NASA footage: {f}")
                    return f
    except Exception as e:
        print(f"Notice in NASA search: {e}")

    # Fallback to high-quality default space footage
    fallback = "https://images-assets.nasa.gov/video/301_BlackHoles/301_BlackHoles~orig.mp4"
    print(f"Using verified cosmic archive footage: {fallback}")
    return fallback

def process_viral_short(youtube_url, upload=False):
    print("=" * 60)
    print("SCIBYTES VIRAL REVERSE ENGINEERING & CAPCUT GENERATOR")
    print(f"Target Video URL: {youtube_url}")
    print("=" * 60)

    # Clean previous output to prevent showing old video on error
    output_video = os.path.join(PROJECT_ROOT, 'output', 'scibytes_short_latest.mp4')
    if os.path.exists(output_video):
        try:
            os.remove(output_video)
        except Exception:
            pass

    # Step 1: Extract Transcript
    ext = extract_transcript_from_url(youtube_url)
    raw_title = ext['title']
    raw_transcript = ext['transcript']

    # Step 2: AI Re-engineer Script
    print("\nRe-engineering script with AI for peak retention & originality...")
    reengineered = reengineer_script(raw_title, raw_transcript)
    print(f"Title: {reengineered['title']}")
    print(f"Script: {reengineered['script']}")

    # Step 3: Match Footage
    footage_url = search_matching_nasa_footage(reengineered.get('keywords', ['space', 'universe']))

    # Step 4: Construct Topic Object
    clean_id = "viral_" + "".join(c for c in reengineered['title'] if c.isalnum() or c in ('_', '-')).lower()[:25]
    topic = {
        "id": clean_id,
        "title": reengineered['title'],
        "top_header": reengineered.get('top_header', 'SCIBYTES DAILY'),
        "sub_header": reengineered.get('sub_header', reengineered['title'].split('#')[0].strip()),
        "script": reengineered['script'],
        "framing_mode": "fullscreen",
        "start_offset": 6.0,
        "subtitles": [],
        "footage_url": footage_url
    }

    # Step 5: Build Video (Voiceover, CapCut Subtitles, Audio Mastering, BGM)
    print("\nBuilding video with ElevenLabs voiceover, CapCut subtitles, and BGM...")
    build_short_pipeline(topic)

    # Step 6: Generate Full SEO Metadata
    seo = generate_seo_metadata(topic)
    meta_path = os.path.join('output', 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(seo, f, indent=2)
    print(f"SEO metadata saved: {meta_path}")

    # Step 7: Optional Direct Upload
    if upload:
        print("\nUploading finished Short to YouTube Studio...")
        from pipeline.upload_to_youtube import get_authenticated_service, upload_video
        youtube = get_authenticated_service()
        upload_video(youtube, topic)

    print("\n" + "=" * 60)
    print("VIRAL SHORT GENERATION COMPLETE!")
    print("Video output: output/scibytes_short_latest.mp4")
    print("Thumbnail output: output/thumbnail.jpg")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create SciBytes Short from any viral YouTube link")
    parser.add_argument('--url', required=True, help="YouTube Short or Video URL to replicate")
    parser.add_argument('--upload', action='store_true', help="Upload directly to YouTube upon completion")
    args = parser.parse_args()

    try:
        process_viral_short(args.url, upload=args.upload)
    except Exception as e:
        print("\n" + "!" * 60)
        print(f"PIPELINE ERROR: {e}")
        print("!" * 60)
        sys.exit(1)
