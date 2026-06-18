import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()

from apps.home.models import TeamMember

members = TeamMember.objects.all()
for member in members:
    print(member.name)
