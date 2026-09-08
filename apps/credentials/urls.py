from django.urls import re_path

from . import views

app_name = 'credentials'

# A bounded character class, not <slug:code>: slug allows underscores and has no
# length limit, so garbage would reach the view and the database. This rejects it
# at the routing layer instead.
CODE = r'(?P<code>[0-9A-Za-z\-]{10,20})'

urlpatterns = [
    re_path(r'^verify/$', views.verify_lookup, name='lookup'),

    # Canonical form, with the trailing slash. Listed first so reverse() builds
    # this URL for canonical links and redirects.
    re_path(rf'^verify/{CODE}/$', views.verify_detail, name='detail'),

    # Slash-less alias. CommonMiddleware's APPEND_SLASH would otherwise 301 it,
    # costing an extra round trip on every QR scan -- and some reader apps warn
    # the user when a link redirects.
    re_path(rf'^verify/{CODE}$', views.verify_detail, name='detail_noslash'),

    # Short form, encoded in the QR to keep the printed symbol small.
    re_path(rf'^v/{CODE}/?$', views.verify_detail, name='detail_short'),

    # Uppercase aliases. qr.build_payload() uppercases the WHOLE URL so the
    # symbol stays in QR alphanumeric mode (lowercase would force byte mode and
    # cost a version), which means the printed QR encodes /V/ -- not /v/.
    # Hostnames are case-insensitive, paths are not, so without these routes
    # every printed QR would 404. Separate patterns rather than a case-insensitive
    # regex because reverse() cannot build a URL from a character class, and the
    # lowercase routes above must stay the canonical reversible ones.
    re_path(rf'^V/{CODE}/?$', views.verify_detail, name='detail_short_upper'),
    re_path(rf'^VERIFY/{CODE}/?$', views.verify_detail, name='detail_upper'),
    re_path(r'^VERIFY/$', views.verify_lookup, name='lookup_upper'),
]
