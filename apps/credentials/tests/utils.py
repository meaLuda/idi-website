"""Shared test helpers."""

from django.test import override_settings

# Tests must not touch the shared dev-valkey instance: Django's RedisCache.clear()
# flushes the whole database index, not just this project's key prefix. An
# in-memory cache also makes throttle counters deterministic per test.
isolated_cache = override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'credentials-tests',
        }
    }
)
