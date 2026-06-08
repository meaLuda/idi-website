import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()

from apps.home.models import TeamMember

updates = {
    'Pauline': 'uploads/team/2J7A4647.jpg',
    'Munyala': 'uploads/team/2J7A4683.jpg',
    'Denise': 'uploads/team/2J7A4504.jpg',
    'Ryan': 'uploads/team/2J7A4556.jpg',
    'Rose': 'uploads/team/2J7A4473.jpg',
    'Major': 'uploads/team/2J7A4579.jpg',
}

members = TeamMember.objects.all()

for member in members:
    for key, img_path in updates.items():
        if key.lower() in member.name.lower():
            member.image = img_path
            member.save()
            print(f"Updated {member.name} -> {img_path}")
            break
