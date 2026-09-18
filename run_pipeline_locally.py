import os
import sys
import subprocess

print("=" * 60)
print("SciBytes - Local Pipeline Test Runner")
print("=" * 60)

print("\nStep 1: Running pipeline/build_short.py...")
res = subprocess.run([sys.executable, "pipeline/build_short.py"])

if res.returncode == 0:
    print("\n" + "=" * 60)
    print("SUCCESS: Video and metadata generated successfully!")
    print("Output video: output/scibytes_short_latest.mp4")
    print("Metadata:     output/metadata.json")
    print("=" * 60)
else:
    print("\nERROR: Video generation failed with return code:", res.returncode)
