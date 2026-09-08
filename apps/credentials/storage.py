"""Private storage for archived certificate PDFs.

The default media storage is world-readable. ``AWS_QUERYSTRING_AUTH = False`` in
settings, the Garage bucket is website-enabled, and ``deploy/traefik/idi-s3-proxy.yml``
proxies ``/media/*`` while stamping ``Cache-Control: public, max-age=31536000,
immutable``. A plain ``FileField(upload_to='uploads/certificates/')`` would
therefore publish every graduate's certificate PDF at a stable public URL, cached
for a year -- and deleting the object would not un-cache the copies already served.

So certificate PDFs go to a SEPARATE bucket, not merely a different prefix: the
website flag is per-bucket in Garage, and the Traefik router matches the whole
``/media/`` prefix. With ``querystring_auth`` on, admin links are short-lived
presigned URLs and nothing in the public proxy path matches them.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages


def certificate_storage():
    """Resolve the private storage backend lazily.

    A callable, not an instance: ``FileField(storage=...)`` serialises a callable
    by reference, so migrations do not freeze a bound backend configuration.
    """
    try:
        return storages['certificates']
    except Exception:
        # Local development without the private bucket configured. Kept outside
        # MEDIA_ROOT so it is never reachable through the /media/ URL route.
        return FileSystemStorage(
            location=str(settings.BASE_DIR / 'private_media' / 'certificates'),
            base_url=None,
        )


def certificate_pdf_path(instance, filename):
    """Build an unguessable storage path.

    The client-supplied filename is discarded entirely -- it is attacker
    controlled, and ``get_valid_filename`` is not a security boundary. A random
    suffix means the path is not derivable from the certificate serial, which is
    defence in depth if this ever lands in public storage. It is not access
    control on its own.
    """
    year = instance.issue_date.year if instance.issue_date else 'unknown'
    token = (instance.token or 'pending')[:12]
    return f'certificates/{year}/{token[:2]}/{token}-{secrets.token_hex(8)}.pdf'
