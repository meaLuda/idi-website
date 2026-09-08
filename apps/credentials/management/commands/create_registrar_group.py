"""Create the Registrar group: can issue certificates, cannot touch the website.

Keeping issuance and marketing-site editing in separate permission sets is one of
the reasons credentials lives in its own app.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

GROUP_NAME = 'Registrar'

PERMISSIONS = [
    ('credentials', 'certificate', ['add', 'change', 'view']),
    ('credentials', 'cohort', ['add', 'change', 'view']),
    ('credentials', 'certificatescan', ['view']),
    ('credentials', 'certificateauditevent', ['view']),
]


class Command(BaseCommand):
    help = 'Create or update the Registrar group used to issue DIDA certificates.'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=GROUP_NAME)
        wanted = []
        for app_label, model, actions in PERMISSIONS:
            for action in actions:
                permission = Permission.objects.filter(
                    content_type__app_label=app_label,
                    content_type__model=model,
                    codename=f'{action}_{model}',
                ).first()
                if permission:
                    wanted.append(permission)
                else:
                    self.stderr.write(f'Missing permission: {action}_{model}')

        group.permissions.set(wanted)
        verb = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} group "{GROUP_NAME}" with {len(wanted)} permission(s). '
            'It grants no access to apps.home.'
        ))
