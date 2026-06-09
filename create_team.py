import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()

from apps.home.models import TeamMember

new_members = [
    {
        'name': 'Ryan Maninga',
        'position': 'Environment Lead & Design Researcher',
        'image': 'uploads/team/2J7A4556.jpg',
        'bio': '<p>Environment Lead & Design Researcher at IDI Africa.</p>'
    },
    {
        'name': 'Rose Njenga',
        'position': 'Health Lead & Design Researcher',
        'image': 'uploads/team/2J7A4473.jpg',
        'bio': '<p>Health Lead & Design Researcher at IDI Africa.</p>'
    },
    {
        'name': 'Major Maina',
        'position': 'Food Systems Lead & Design Researcher',
        'image': 'uploads/team/2J7A4579.jpg',
        'bio': '<p>Food Systems Lead & Design Researcher at IDI Africa.</p>'
    }
]

for m in new_members:
    obj, created = TeamMember.objects.get_or_create(
        name=m['name'],
        defaults={
            'position': m['position'],
            'image': m['image'],
            'bio': m['bio']
        }
    )
    if not created:
        obj.position = m['position']
        obj.image = m['image']
        obj.save()
    print(f"{'Created' if created else 'Updated'} {obj.name}")
