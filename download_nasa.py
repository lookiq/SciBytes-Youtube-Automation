import requests

url = 'https://images-assets.nasa.gov/video/GSFC_20130314_Jupiter_m11204_HotSpots/GSFC_20130314_Jupiter_m11204_HotSpots~medium.mp4'
print("Downloading NASA real Jupiter clip...")
r = requests.get(url, stream=True)
with open("nasa_jupiter_raw.mp4", "wb") as f:
    for chunk in r.iter_content(chunk_size=1024*1024):
        if chunk:
            f.write(chunk)
print("NASA clip downloaded successfully: nasa_jupiter_raw.mp4")
