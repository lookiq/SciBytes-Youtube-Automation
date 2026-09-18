import requests

url = "https://images-api.nasa.gov/search?q=jupiter&media_type=video"
r = requests.get(url).json()
items = r.get('collection', {}).get('items', [])
print(f"Found {len(items)} NASA video items for Jupiter")
if items:
    sample_item = items[0]
    nasa_id = sample_item['data'][0]['nasa_id']
    title = sample_item['data'][0]['title']
    print("Sample title:", title)
    print("NASA ID:", nasa_id)
    # get assets
    asset_url = f"https://images-api.nasa.gov/asset/{nasa_id}"
    asset_r = requests.get(asset_url).json()
    files = [f['href'] for f in asset_r.get('collection', {}).get('items', []) if f['href'].endswith('.mp4')]
    print("MP4 video links:", files[:3])
