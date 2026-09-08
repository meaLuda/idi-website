"""Public certificate verification.

Follows the project's function-based-view convention (see
``apps.home.views.program_detail``): a context dict carrying ``page_title`` /
``page_description`` consumed by ``templates/partials/meta_tags.html``.

Two things differ from every other page on the site and are deliberate:

* ``@never_cache`` and ``X-Robots-Tag``. Traefik already stamps
  ``max-age=31536000, immutable`` on ``/media/*``; if that ever extended to
  ``/verify/`` a revoked certificate would keep reading "Verified" for a year.
* Generic Open Graph text. Pasting a verify link into a WhatsApp or Slack group
  triggers a preview fetch, and a preview card carrying the recipient's name
  would broadcast their credential to that whole group without anyone clicking.
"""

from __future__ import annotations

import logging

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from . import throttle
from .forms import CertificateLookupForm
from .models import Certificate, CertificateScan
from .scans import client_ip, hash_ip, log_scan
from .tokens import format_code, is_valid_code, normalize_code

logger = logging.getLogger(__name__)

NOINDEX = 'noindex, nofollow, noarchive'

# Deliberately identical for "no such code" and "code failed its checksum": the
# page must never confirm that a partially-correct guess is close.
SOCIAL_TITLE = 'Certificate verification'
SOCIAL_DESCRIPTION = (
    'Verify a certificate issued by the Decision Intelligence Design Academy '
    'at the Institute of Design & Innovation.'
)


def _harden(response):
    response['X-Robots-Tag'] = NOINDEX
    return response


def _base_context(request, **extra):
    context = {
        'page_robots': NOINDEX,
        'social_title': SOCIAL_TITLE,
        'social_description': SOCIAL_DESCRIPTION,
        'page_description': SOCIAL_DESCRIPTION,
    }
    context.update(extra)
    return context


def _render_not_found(request, ip_hash, attempted=''):
    """The single response for malformed, unknown and draft codes."""
    allowed, retry_after = throttle.register_failure(ip_hash)
    if not allowed:
        return _render_throttled(request, retry_after)

    context = _base_context(
        request,
        page_title='Certificate not found',
        form=CertificateLookupForm(initial={'ts': CertificateLookupForm.make_timestamp()}),
        # Point canonical at the lookup page rather than the attempted code, so
        # every failed attempt renders an identical document. Echoing the code
        # would make a draft record distinguishable from an unknown one.
        canonical_url=request.build_absolute_uri(reverse('credentials:lookup')),
    )
    response = render(request, 'credentials/verify_not_found.html', context, status=404)
    return _harden(response)


def _render_throttled(request, retry_after):
    context = _base_context(request, page_title='Too many attempts', retry_after=retry_after)
    response = render(request, 'credentials/verify_throttled.html', context, status=429)
    response['Retry-After'] = str(int(retry_after))
    return _harden(response)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def verify_detail(request, code):
    """Resolve a verification code and render its status."""
    ip_hash = hash_ip(client_ip(request))

    allowed, retry_after = throttle.check_lookup(ip_hash)
    if not allowed:
        return _render_throttled(request, retry_after)

    normalized = normalize_code(code)
    method = (
        CertificateScan.Method.QR
        if request.path.startswith('/v/')
        else CertificateScan.Method.DIRECT
    )

    # Checksum first: 31 of every 32 random guesses die here, in pure Python,
    # with zero database queries. Deliberately NOT logged as a scan row -- writing
    # one would let a brute-force attempt grow the scan table without bound, which
    # is exactly what the checksum gate exists to prevent. The throttle still
    # counts the attempt.
    if not is_valid_code(normalized):
        logger.info('Rejected malformed verification code (checksum failed)')
        return _render_not_found(request, ip_hash, attempted=code)

    # .first(), not get_object_or_404: a 404 would route to the site-wide error
    # handler and render a generic "page not found" illustration, which reads as a
    # broken website rather than a verification result.
    certificate = (
        Certificate.objects.select_related('cohort', 'superseded_by')
        .filter(token=normalized)
        .first()
    )
    if certificate is None or certificate.public_state == 'not_found':
        log_scan(request, CertificateScan.Outcome.NOT_FOUND, None, method)
        return _render_not_found(request, ip_hash, attempted=code)

    state = certificate.public_state
    context = _base_context(
        request,
        page_title=f'Certificate {certificate.serial}',
        certificate=certificate,
        state=state,
        token_display=format_code(certificate.token),
        canonical_url=request.build_absolute_uri(
            reverse('credentials:detail', kwargs={'code': certificate.token})
        ),
    )
    response = render(request, 'credentials/verify_detail.html', context, status=200)

    # Render decision first, log second: a logging failure must never affect the
    # response. log_scan() additionally swallows its own exceptions.
    log_scan(request, state, certificate, method)
    return _harden(response)


@never_cache
def verify_lookup(request):
    """Manual code entry, for someone typing the code off a printed certificate."""
    ip_hash = hash_ip(client_ip(request))

    if request.method == 'POST':
        allowed, retry_after = throttle.check_form(ip_hash)
        if not allowed:
            return _render_throttled(request, retry_after)

        form = CertificateLookupForm(request.POST)
        if form.is_valid():
            # Post/Redirect/Get: a refresh must not resubmit, and the resulting
            # URL should be shareable.
            return redirect('credentials:detail', code=form.cleaned_data['code'])
    else:
        form = CertificateLookupForm(initial={'ts': CertificateLookupForm.make_timestamp()})

    context = _base_context(
        request,
        page_title='Verify a certificate',
        form=form,
    )
    response = render(request, 'credentials/verify_lookup.html', context)
    return _harden(response)
