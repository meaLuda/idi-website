"""Rate limiting for certificate verification.

Deliberately fails OPEN. The security control against guessing a code is the 55
bits of entropy in the code itself, not this throttle -- so if the cache is
unreachable, allowing the request is strictly better than taking the verification
page offline. A dark verify page is a total failure; a briefly unthrottled one is
not.

Requires a shared cache. The project previously had no CACHES setting at all,
which meant a per-process LocMemCache across four preloaded gunicorn workers:
counters split four ways and reset unpredictably at --max-requests.
"""

from __future__ import annotations

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

# (limit, window seconds). Tier 1 is deliberately generous: a graduation ceremony
# or an HR department sits behind a single NAT egress IP, and blocking them is a
# worse outcome than allowing a slow scrape.
LIMIT_LOOKUP = (60, 600)        # any verification GET
# Tier 2 is the actual enumeration control. Only FAILED lookups count, so a
# legitimate visitor is never throttled by their own successful checks.
LIMIT_FAILURES = (10, 3600)
LIMIT_FAILURES_DAILY = (100, 86400)
# Tier 3: the manual-entry form.
LIMIT_FORM = (5, 300)


def _hit(scope, identity, limit, window):
    """Increment a counter. Returns (allowed, retry_after_seconds)."""
    if not identity:
        return True, 0
    key = f'verify:{scope}:{identity}'
    try:
        added = cache.add(key, 1, window)
        count = 1 if added else cache.incr(key)
    except ValueError:
        # Key expired between add() and incr(); treat as a fresh window.
        try:
            cache.set(key, 1, window)
            count = 1
        except Exception:
            logger.warning('Rate-limit cache unavailable; failing open', exc_info=True)
            return True, 0
    except Exception:
        logger.warning('Rate-limit cache unavailable; failing open', exc_info=True)
        return True, 0

    if count > limit:
        return False, window
    return True, 0


def check_lookup(ip_hash):
    """Tier 1: overall verification requests."""
    return _hit('lookup', ip_hash, *LIMIT_LOOKUP)


def check_form(ip_hash):
    """Tier 3: manual-entry form submissions."""
    return _hit('form', ip_hash, *LIMIT_FORM)


def register_failure(ip_hash):
    """Tier 2: record a failed lookup and report whether the caller is now over.

    Never keyed on the certificate token -- doing so would let an attacker lock
    a genuine certificate out of verification by hammering its code.
    """
    allowed_hour, retry_hour = _hit('fail1h', ip_hash, *LIMIT_FAILURES)
    allowed_day, retry_day = _hit('fail24h', ip_hash, *LIMIT_FAILURES_DAILY)
    if not allowed_hour:
        return False, retry_hour
    if not allowed_day:
        return False, retry_day
    return True, 0
