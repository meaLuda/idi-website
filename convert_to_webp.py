import os
from PIL import Image

def convert_to_webp(file_path):
    if not (file_path.endswith('.jpg') or file_path.endswith('.png')):
        return file_path
    
    webp_path = file_path.rsplit('.', 1)[0] + '.webp'
    try:
        img = Image.open(file_path)
        img.save(webp_path, 'webp')
        print(f"Converted {file_path} -> {webp_path}")
        return webp_path
    except Exception as e:
        print(f"Error converting {file_path}: {e}")
        return file_path

directories_to_process = [
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\static\images\space_ai",
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\static\images\be_green",
    r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\media\uploads\projects\thumbnails"
]

for d in directories_to_process:
    if os.path.exists(d):
        for f in os.listdir(d):
            full_path = os.path.join(d, f)
            if os.path.isfile(full_path):
                # only convert the ones we recently added or specific formats
                if f in ['img1.jpg', 'img2.jpg', 'img3.jpg', 'img4.jpg', 'img1.png', 'img5.jpg', 'space-ai-card.png', 'be-green-card.png']:
                    convert_to_webp(full_path)
