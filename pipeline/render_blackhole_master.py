import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline.multi_clip_editor import render_multi_clip_short
from pipeline.build_short import generate_voice

def run_render():
    topic = {
        'id': 'viral_whatwouldhappenifablackho',
        'title': 'What If Earth Fell Into a Black Hole? #Shorts',
        'script': "What would actually happen if Earth fell into a black hole? At first, crossing the outer gravitational field, you wouldn't feel a thing. But as our planet inches closer to the event horizon, violent tidal forces would rip our tectonic plates apart! Oceans would instantly vaporize, the crust would shatter into trillions of molten fragments, and extreme gravity would stretch our planet into a ribbon of atoms! Could anything ever escape the singularity? Subscribe to SciBytes to explore the universe."
    }

    clean_sources = [
        os.path.join(PROJECT_ROOT, 'temp', 'earth_cracking_clean.mp4'),
        os.path.join(PROJECT_ROOT, 'temp', 'blackhole_shredding_star.mp4'),
        os.path.join(PROJECT_ROOT, 'temp', 'nasa_goddard_flight_around_blackhole.mp4'),
        os.path.join(PROJECT_ROOT, 'temp', 'fall_blackhole_15s.mp4'),
        os.path.join(PROJECT_ROOT, 'temp', 'black_hole_spaghettification_raw.mp4'),
        os.path.join(PROJECT_ROOT, 'temp', 'nasa_blackhole_eats_star.mp4')
    ]

    audio_path = os.path.join(PROJECT_ROOT, 'temp', 'viral_whatwouldhappenifablackho_voice.mp3')
    ass_path = os.path.join(PROJECT_ROOT, 'temp', 'viral_whatwouldhappenifablackho_subs.ass')
    output_path = os.path.join(PROJECT_ROOT, 'output', 'scibytes_short_latest.mp4')

    print("=" * 60)
    print("SCIBYTES CLEAN MASTER RENDER (NO TOP CARD, ZERO TEXT, LOUD VOICE)")
    print("=" * 60)
    print("Generating 30s studio-mastered voiceover and dynamic subtitles...")
    generate_voice(topic['script'], audio_path, ass_path)
    for i, s in enumerate(clean_sources):
        print(f"Source {i+1}: {os.path.basename(s)} (Exists: {os.path.exists(s)})")

    render_multi_clip_short(
        topic=topic,
        clip_sources=clean_sources,
        audio_path=audio_path,
        output_path=output_path,
        ass_path=ass_path,
        show_top_card=False
    )
    print("=" * 60)
    print("MASTER RENDER COMPLETE!")
    print(f"Output: {output_path}")
    print("=" * 60)

if __name__ == '__main__':
    run_render()
