import os
import re

template_dir = r"c:\Users\User\Desktop\IDI WEBSITE\idi-website\templates"

# Regex to find <img ...> tags
img_pattern = re.compile(r'(<img\b[^>]*>)', re.IGNORECASE)

def add_lazy_loading(match):
    img_tag = match.group(1)
    # If loading= is already present, don't modify
    if re.search(r'\bloading\s*=', img_tag, re.IGNORECASE):
        return img_tag
    
    # Insert loading="lazy" before the closing bracket
    if img_tag.endswith('/>'):
        return img_tag[:-2] + ' loading="lazy" />'
    else:
        return img_tag[:-1] + ' loading="lazy">'

count = 0
for root, _, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = img_pattern.sub(add_lazy_loading, content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"Updated {file_path}")

print(f"Applied lazy loading to {count} files.")
