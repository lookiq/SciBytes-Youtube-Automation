from copy_scibytes_top_seo import seo_desc

print(f"Total Characters (with spaces): {len(seo_desc)}")
print(f"Total Characters (without spaces): {len(seo_desc.replace(' ', '').replace('\n', ''))}")
print(f"Total Words: {len(seo_desc.split())}")
