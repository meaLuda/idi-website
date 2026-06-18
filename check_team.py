import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()

from apps.home.models import TeamMember

members = TeamMember.objects.all()
for m in members:
    has_image = bool(m.image)
    print(f"ID: {m.id} | Name: {m.name} | Image: {m.image} | Position: {m.position}")
