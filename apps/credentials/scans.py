"""Verification scan logging.

Every lookup is recorded, de-duplicated to one row per person per certificate per
day. Three properties matter more than the analytics:

1. **It must never break verification.** Logging happens after the response
   context is built and is wrapped so any failure degrades to a log line. A page
   that 500s because the scan table is locked has failed at the only job it has.
2. **It must not store personal data in the clear.** Under Kenya's Data
   Protection Act 2019 and GDPR an IP address identifies a person.
3. **It must not mistake link-preview bots for people.** WhatsApp is the dominant
   sharing channel here and fetches a URL the moment it is pasted.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Certificate, CertificateScan

logger = logging.getLogger(__name__)

# Substrings identifying automated clients. Link-preview unfurlers come first
# because they are the largest real source of phantom "scans".
BOT_MARKERS = (
    'whatsapp', 'slackbot', 'telegram', 'discord', 'twitterbot', 'linkedin',
    'facebookexternalhit', 'skypeuripreview', 'embedly', 'pinterest', 'vkshare',
    'bot', 'crawler', 'spider', 'slurp', 'preview', 'scrapy',
    'python-requests', 'curl', 'wget', 'go-http-client', 'okhttp', 'headlesschrome',
)

# Coarse family labels. Deliberately low-resolution: a full user-agent string is a
# usable browser fingerprint, so only a hash and a broad label are stored.
_UA_FAMILIES = (
    ('whatsapp', 'whatsapp'),
    ('slackbot', 'slack'),
    ('telegram', 'telegram'),
    ('facebookexternalhit', 'facebook'),
    ('linkedinbot', 'linkedin'),
    ('twitterbot', 'twitter'),
    ('iphone', 'ios'),
    ('ipad', 'ios'),
    ('android', 'android'),
    ('macintosh', 'macos'),
    ('windows', 'windows'),
    ('linux', 'linux'),
)


def client_ip(request):
    """Return the caller's IP address, or '' when it cannot be determined.

    Traefik terminates TLS and *appends* the real client to X-Forwarded-For, so
    the trustworthy entry is counted from the RIGHT. The common
    ``xff.split(',')[0]`` idiom takes the leftmost value, which is entirely
    client-supplied -- an attacker sets their own header and defeats the rate
    limiter. Conversely, ignoring the header altogether makes every request look
    like the proxy, which collapses de-duplication and means the first abuser
    throttles every legitimate visitor on the planet.
    """
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        parts = [p.strip() for p in forwarded.split(',') if p.strip()]
        hops = max(1, getattr(settings, 'TRUSTED_PROXY_HOPS', 1))
        if len(parts) >= hops:
            candidate = parts[-hops]
            if _is_ip(candidate):
                return candidate
    remote = request.META.get('REMOTE_ADDR', '')
    return remote if _is_ip(remote) else ''


def _is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def hash_ip(ip, day=None):
    """Return a salted, date-bucketed hash of an IP address.

    The salt is the entire privacy control: an unsalted SHA-256 of an IPv4 address
    covers only 2**32 inputs and is reversible in seconds. Do not remove it, and
    do not replace it with SECRET_KEY -- rotating the secret key is a routine
    security action that must not de-anonymise this log or break de-duplication.

    Including the date makes hashes unlinkable across days, which is exactly the
    granularity de-duplication needs and nothing more.
    """
    if not ip:
        return ''
    day = day or timezone.localdate()
    salt = getattr(settings, 'SCAN_IP_SALT', '')
    return hashlib.sha256(f'{salt}|{ip}|{day.isoformat()}'.encode()).hexdigest()


def classify_user_agent(user_agent):
    """Return ``(is_bot, family)`` for a user-agent string."""
    if not user_agent:
        # No UA at all is not a browser. Treat as automated rather than counting
        # it as a human verification.
        return True, 'unknown'
    lowered = user_agent.lower()
    is_bot = any(marker in lowered for marker in BOT_MARKERS)
    family = 'other'
    for marker, label in _UA_FAMILIES:
        if marker in lowered:
            family = label
            break
    return is_bot, family


def _referer_host(request):
    referer = request.META.get('HTTP_REFERER', '')
    if not referer:
        return ''
    try:
        return (urlparse(referer).hostname or '')[:120]
    except ValueError:
        return ''


def log_scan(request, outcome, certificate=None, method=CertificateScan.Method.DIRECT):
    """Record one verification lookup. Never raises.

    Returns the CertificateScan row, or None if logging failed or was skipped.
    """
    try:
        return _log_scan(request, outcome, certificate, method)
    except Exception:
        # Deliberately broad: verification must succeed even if logging cannot.
        logger.warning('Failed to log certificate scan', exc_info=True)
        return None


def _log_scan(request, outcome, certificate, method):
    now = timezone.now()
    day = timezone.localdate()

    ip = client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:512]
    is_bot, family = classify_user_agent(user_agent)

    ip_hash = hash_ip(ip, day)
    ua_hash = hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else ''
    dedupe_key = CertificateScan.build_dedupe_key(
        certificate.pk if certificate else None, ip_hash, ua_hash, day,
    )

    # Nested atomic block: on PostgreSQL a failed statement otherwise poisons the
    # surrounding transaction for the rest of the request.
    with transaction.atomic():
        scan, created = CertificateScan.objects.get_or_create(
            dedupe_key=dedupe_key,
            defaults={
                'certificate': certificate,
                'certificate_serial': certificate.serial if certificate else '',
                'scanned_at': now,
                'outcome': outcome,
                'lookup_method': method,
                'ip_hash': ip_hash,
                'ua_hash': ua_hash,
                'ua_family': family,
                'is_bot': is_bot,
                'referer_host': _referer_host(request),
            },
        )
        if not created:
            # Same person, same certificate, same day: count the extra visit
            # rather than creating a row. F() so concurrent workers do not race.
            CertificateScan.objects.filter(pk=scan.pk).update(
                hit_count=F('hit_count') + 1, scanned_at=now,
            )
            return scan

        # Only genuinely new, non-bot visits move the public counter. Bots are
        # recorded but excluded, so we can still see how much traffic was unfurls.
        if certificate is not None and not is_bot:
            updates = {'scan_count': F('scan_count') + 1, 'last_scanned_at': now}
            if certificate.first_scanned_at is None:
                updates['first_scanned_at'] = now
            # .update() bypasses save(), which is correct here: a scan is not an
            # edit of the certificate, so it must not trip the immutability guard
            # or bump updated_at.
            Certificate.objects.filter(pk=certificate.pk).update(**updates)
    return scan
