import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()

from apps.home.models import TeamMember

# Delete Ramah Madiba and Sarah Mpapuluu
TeamMember.objects.filter(name__in=["Ramah Madiba", "Sarah Mpapuluu"]).delete()
print("Deleted empty team members.")
