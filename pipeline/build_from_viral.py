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
    from pipeline.cinematic_footage_engine import get_cinematic_space_footage
except ImportError:
    from transcript_engine import extract_transcript_from_url
    from script_reengineer import reengineer_script
    from build_short import build_short_pipeline
    from seo_engine import generate_seo_metadata
    from cinematic_footage_engine import get_cinematic_space_footage

def search_matching_nasa_footage(keywords):
    query = " ".join(keywords) if isinstance(keywords, list) else str(keywords)
    return get_cinematic_space_footage(query)

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

    # Save direct copies to User's Desktop
    desktop_dir = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
    desktop_video = os.path.join(desktop_dir, 'SciBytes_Viral_Short_Preview.mp4')
    desktop_thumb = os.path.join(desktop_dir, 'SciBytes_Thumbnail_Preview.jpg')
    try:
        import shutil
        if os.path.exists(output_video):
            shutil.copy2(output_video, desktop_video)
            print(f"Direct Desktop video saved: {desktop_video}")
        thumb_path = os.path.join('output', 'thumbnail.jpg')
        if os.path.exists(thumb_path):
            shutil.copy2(thumb_path, desktop_thumb)
            print(f"Direct Desktop thumbnail saved: {desktop_thumb}")
    except Exception as e:
        print(f"Desktop copy notice: {e}")

    print("\n" + "=" * 60)
    print("VIRAL SHORT GENERATION COMPLETE!")
    print(f"Desktop Preview : {desktop_video}")
    print("Video output    : output/scibytes_short_latest.mp4")
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
