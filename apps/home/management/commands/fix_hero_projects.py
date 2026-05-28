from django.core.management.base import BaseCommand
from apps.home.models import Project


class Command(BaseCommand):
    help = 'Fix hero project cards to show exactly the 5 specified projects'

    def handle(self, *args, **options):
        # Deactivate unwanted projects
        for title in ['Sovereign Data Infrastructure', 'Community Public-Service Redesign']:
            n = Project.objects.filter(title=title).update(is_active=False)
            self.stdout.write(f'Deactivated {n} x "{title}"')

        # Deactivate the extra E4Impact at order=3
        n = Project.objects.filter(title='E4Impact Accelerator Program', order=3).update(is_active=False)
        self.stdout.write(f'Deactivated {n} x extra E4Impact (order=3)')

        # Set display order for the 5 keepers
        Project.objects.filter(title='National Digital Identity Framework').update(order=0)
        Project.objects.filter(title='AI Ethics & Governance Toolkit').update(order=1)
        Project.objects.filter(title='E4Impact Accelerator Program', is_active=True).update(order=2)
        Project.objects.filter(title='The Mombasa County Plastics Prize').update(order=3)

        self.stdout.write('\n--- Active projects in display order ---')
        for p in Project.objects.filter(is_active=True).order_by('order', '-created_at'):
            self.stdout.write(f'  order={p.order} | {p.title}')

        self.stdout.write(self.style.SUCCESS('\nDone!'))
