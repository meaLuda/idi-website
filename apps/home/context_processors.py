from django.conf import settings


def site(request):
    """Expose site-wide values (analytics id, debug flag) to all templates."""
    return {
        'ga_measurement_id': getattr(settings, 'GA_MEASUREMENT_ID', ''),
        'site_debug': settings.DEBUG,
    }
