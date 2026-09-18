import asyncio
import os
import subprocess
import edge_tts

SCRIPT_TEXT = (
    "If you fall into a black hole, you won't just be crushed. "
    "You will literally be stretched into a single strand of human spaghetti. "
    "This terrifying process is called Spaghettification. "
    "Because gravity is millions of times stronger at your feet than your head, "
    "your body gets stretched out like an ultra-thin cosmic noodle. "
    "And to anyone watching from the outside, time slows down so much "
    "that you would appear frozen at the edge of the event horizon forever. "
    "Subscribe to Daily Dose of Physics for more mind-bending space mysteries!"
)

TITLE = "What Happens If You Fall Into a Black Hole? 🌌 #Shorts"
DESCRIPTION = """What happens if you fall into a black hole? Prepare for Spaghettification! 🌌🕳️

Subscribe to Daily Dose of Physics for daily mind-bending science facts, quantum mechanics, and cosmic wonders!

#DailyDoseOfPhysics #BlackHole #SpaceFacts #Physics #Astronomy #ScienceFacts #Shorts #Cosmology
"""

async def make_audio():
    print("Generating voiceover with Edge-TTS...")
    communicate = edge_tts.Communicate(SCRIPT_TEXT, "en-US-ChristopherNeural", rate="+5%")
    await communicate.save("audio.mp3")
    print("Voiceover created: audio.mp3")

def make_video():
    print("Rendering 1080x1920 vertical Short with FFmpeg...")
    ffprobe_cmd = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.mp3'
    duration = float(subprocess.check_output(ffprobe_cmd, shell=True, text=True).strip())
    print(f"Audio duration: {duration:.2f} seconds")

    ffmpeg_cmd = (
        f'ffmpeg -y -f lavfi -i "color=c=#050510:s=1080x1920:d={duration}" '
        f'-f lavfi -i "mandelbrot=s=1080x1920:rate=30:maxiter=120" '
        f'-i audio.mp3 '
        f'-filter_complex "'
        f'[1:v]format=yuv420p,hue=s=0.7:h=240,eq=contrast=1.3:brightness=-0.3[stars]; '
        f'[0:v][stars]blend=all_mode=screen[bg]; '
        f'[bg]drawtext=text=\'DAILY DOSE OF PHYSICS\':fontcolor=yellow:fontsize=48:x=(w-text_w)/2:y=180:box=1:boxcolor=black@0.7:boxborderw=15, '
        f'drawtext=text=\'WHAT HAPPENS IF YOU FALL INTO A BLACK HOLE?\':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=320:box=1:boxcolor=black@0.8:boxborderw=20, '
        f'drawtext=text=\'SPAGHETTIFICATION\':fontcolor=#FF3366:fontsize=64:x=(w-text_w)/2:y=850:enable=\'between(t,5,15)\':box=1:boxcolor=black@0.8:boxborderw=20, '
        f'drawtext=text=\'TIME STOPS AT THE EVENT HORIZON\':fontcolor=#00FFFF:fontsize=50:x=(w-text_w)/2:y=850:enable=\'between(t,15,22)\':box=1:boxcolor=black@0.8:boxborderw=20, '
        f'drawtext=text=\'SUBSCRIBE FOR MORE!\':fontcolor=#FFCC00:fontsize=60:x=(w-text_w)/2:y=1500:box=1:boxcolor=red@0.8:boxborderw=20[outv]" '
        f'-map "[outv]" -map 2:a -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 192k -shortest "Daily_Dose_of_Physics_Black_Hole.mp4"'
    )
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print("Video rendered successfully: Daily_Dose_of_Physics_Black_Hole.mp4")

if __name__ == "__main__":
    asyncio.run(make_audio())
    make_video()
