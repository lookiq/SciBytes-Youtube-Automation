import os
import subprocess

voice_file = "temp/scibytes_kinetic_voice.mp3"
video_in = "temp/reference_short.webm"
video_out = "output/SciBytes_Impossible_Kinetic_Illusion.mp4"
font = "C\\:/Windows/Fonts/ariblk.ttf"

ffprobe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{voice_file}"'
duration = float(subprocess.check_output(ffprobe_cmd, shell=True, text=True).strip())
print(f"Target duration: {duration:.2f}s")

filter_complex = (
    f"[0:v]trim=duration={duration},setpts=PTS-STARTPTS,"
    f"crop=1080:1530:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    f"eq=contrast=1.10:saturation=1.18:brightness=0.01,"
    f"drawtext=fontfile='{font}':text='SCIBYTES':fontcolor=#888888:fontsize=52:x=(w-text_w)/2:y=1750:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{font}':text='MIND-BENDING PHYSICS':fontcolor=#FFEA00:fontsize=36:x=(w-text_w)/2:y=170:borderw=4:bordercolor=black:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{font}':text='IMPOSSIBLE OPTICAL ILLUSION':fontcolor=#FFFFFF:fontsize=46:x=(w-text_w)/2:y=240:borderw=5:bordercolor=black:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
    f"drawtext=fontfile='{font}':text='TWO RINGS PASSING THROUGH?':fontcolor=#FFFFFF:fontsize=52:x=(w-text_w)/2:y=1380:enable='between(t,0,4.5)':borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4,"
    f"drawtext=fontfile='{font}':text='IT IS A SINGLE STRAND!':fontcolor=#00FFFF:fontsize=52:x=(w-text_w)/2:y=1380:enable='between(t,4.5,9.5)':borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4,"
    f"drawtext=fontfile='{font}':text='3D HELICAL KINETIC WAVE':fontcolor=#FFEA00:fontsize=52:x=(w-text_w)/2:y=1380:enable='between(t,9.5,15.0)':borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4,"
    f"drawtext=fontfile='{font}':text='BRAIN CANT TRACK DEPTH!':fontcolor=#FF2A55:fontsize=52:x=(w-text_w)/2:y=1380:enable='between(t,15.0,20.5)':borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4,"
    f"drawtext=fontfile='{font}':text='SUBSCRIBE TO SCIBYTES!':fontcolor=#00FF66:fontsize=52:x=(w-text_w)/2:y=1380:enable='between(t,20.5,{duration})':borderw=6:bordercolor=black:shadowcolor=black@0.95:shadowx=4:shadowy=4[outv]"
)

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", video_in,
    "-i", voice_file,
    "-filter_complex", filter_complex,
    "-map", "[outv]",
    "-map", "1:a",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    video_out
]

print("Rendering high-retention SciBytes Short with Arial Black font...")
subprocess.run(ffmpeg_cmd, check=True)
print(f"Render complete: {video_out}")
