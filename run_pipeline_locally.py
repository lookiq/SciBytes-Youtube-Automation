import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("SciBytes - Local Pipeline Test Runner")
    print("=" * 60)
    print("Running video builder locally...")

    cmd = [sys.executable, "pipeline/build_short.py"]
    res = subprocess.run(cmd)

    if res.returncode == 0:
        video_path = os.path.abspath("output/scibytes_short_latest.mp4")
        metadata_path = os.path.abspath("output/metadata.json")
        print("\n" + "=" * 60)
        print("SUCCESS! Test video rendered successfully.")
        print(f"Video Path: {video_path}")
        print(f"Metadata  : {metadata_path}")
        print("=" * 60)

        # Open in Explorer
        if sys.platform == "win32":
            subprocess.run(f'explorer /select,"{video_path}"', shell=True)
    else:
        print("\nERROR: Video generation failed. Check errors above.")

if __name__ == "__main__":
    main()
