"""Delete old scan rows.

Failed-lookup rows are the ones that grow under an enumeration attempt, so they
expire sooner. Aggregate counters on the certificate (scan_count,
first_scanned_at, last_scanned_at) are never touched and are kept indefinitely.

Run from cron or `docker exec`. Deliberately not Celery -- there is no broker in
this project and this does not justify introducing one.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.credentials.models import CertificateScan

MISS_OUTCOMES = (CertificateScan.Outcome.NOT_FOUND, CertificateScan.Outcome.MALFORMED)
DEFAULT_MISS_DAYS = 30
DEFAULT_HIT_DAYS = 180


class Command(BaseCommand):
    help = 'Purge certificate scan logs past their retention window.'

    def add_arguments(self, parser):
        parser.add_argument('--miss-days', type=int, default=DEFAULT_MISS_DAYS,
                            help=f'Retention for failed lookups (default {DEFAULT_MISS_DAYS}).')
        parser.add_argument('--hit-days', type=int, default=DEFAULT_HIT_DAYS,
                            help=f'Retention for successful lookups (default {DEFAULT_HIT_DAYS}).')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be deleted without deleting it.')

    def handle(self, *args, **options):
        now = timezone.now()
        misses = CertificateScan.objects.filter(
            outcome__in=MISS_OUTCOMES,
            scanned_at__lt=now - timedelta(days=options['miss_days']),
        )
        hits = CertificateScan.objects.filter(
            scanned_at__lt=now - timedelta(days=options['hit_days']),
        ).exclude(outcome__in=MISS_OUTCOMES)

        miss_count, hit_count = misses.count(), hits.count()

        if options['dry_run']:
            self.stdout.write(
                f'Would delete {miss_count} failed-lookup row(s) older than '
                f'{options["miss_days"]}d and {hit_count} successful row(s) older '
                f'than {options["hit_days"]}d.'
            )
            return

        misses.delete()
        hits.delete()
        self.stdout.write(self.style.SUCCESS(
            f'Deleted {miss_count + hit_count} scan row(s) '
            f'({miss_count} failed, {hit_count} successful). '
            'Certificate scan counters are unaffected.'
        ))
