import os
from PIL import Image

directories = [
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\static\images\core_principles",
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\media\uploads\team",
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\static\images\services"
]

MAX_SIZE = (800, 800)
count = 0

for directory in directories:
    if not os.path.exists(directory):
        continue
        
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(directory, filename)
            try:
                with Image.open(file_path) as img:
                    # Only resize if it's larger than MAX_SIZE
                    if img.width > MAX_SIZE[0] or img.height > MAX_SIZE[1]:
                        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
                        
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                            
                        # Overwrite original to maintain references, but highly compressed
                        img.save(file_path, optimize=True, quality=60)
                        print(f"Resized and compressed {filename}")
                        count += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")

print(f"Successfully optimized {count} images.")
