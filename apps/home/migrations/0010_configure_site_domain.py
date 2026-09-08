import os

from django.db import migrations

DEFAULT_DOMAIN = 'idi.africa'
DEFAULT_NAME = 'IDI Africa'


def set_site_domain(apps, schema_editor):
    """Point django.contrib.sites at the real domain.

    django.contrib.sites is installed with SITE_ID = 1, so Django's sitemap
    framework builds every <loc> from Site.objects.get_current(). The row was
    still Django's default 'example.com', which meant /sitemap.xml published
    URLs like http://example.com/team/ -- every entry pointing at a domain the
    organisation does not own, rendering the sitemap useless to crawlers.
    """
    Site = apps.get_model('sites', 'Site')
    domain = os.getenv('SITE_DOMAIN', DEFAULT_DOMAIN)
    Site.objects.update_or_create(
        pk=1, defaults={'domain': domain, 'name': DEFAULT_NAME},
    )


def unset_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=1).update(domain='example.com', name='example.com')


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0009_teammember_timestamps'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, unset_site_domain),
    ]
