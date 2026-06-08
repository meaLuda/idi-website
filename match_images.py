import os
import glob
from PIL import Image
import imagehash

# The 3 uploaded images
uploaded_images = {
    'engage1': r'C:\Users\User\.gemini\antigravity-ide\brain\f5be55d8-6e28-4c2f-8ae9-d747b1952431\media__1780421438472.jpg',
    'engage3': r'C:\Users\User\.gemini\antigravity-ide\brain\f5be55d8-6e28-4c2f-8ae9-d747b1952431\media__1780421440284.jpg',
    'engage4': r'C:\Users\User\.gemini\antigravity-ide\brain\f5be55d8-6e28-4c2f-8ae9-d747b1952431\media__1780421499268.jpg'
}

photos_dir = r'c:\Users\User\Desktop\IDI WEBSITE\idi-website\photos'
hq_photos = glob.glob(os.path.join(photos_dir, '*.jpg'))

hq_hashes = []
for hq in hq_photos:
    try:
        hash_val = imagehash.phash(Image.open(hq))
        hq_hashes.append((hq, hash_val))
    except Exception as e:
        print(f"Error processing {hq}: {e}")

for name, path in uploaded_images.items():
    try:
        up_hash = imagehash.phash(Image.open(path))
        best_match = None
        best_diff = float('inf')
        for hq, hq_hash in hq_hashes:
            diff = up_hash - hq_hash
            if diff < best_diff:
                best_diff = diff
                best_match = hq
        print(f"Match for {name}: {os.path.basename(best_match)} (diff: {best_diff})")
    except Exception as e:
        print(f"Error processing {path}: {e}")
