"""Admin for issuing and managing certificates.

Designed around the real workflow: a registrar issuing certificates one at a time
after a cohort finishes. Picking the cohort pre-fills the snapshot fields, so the
per-certificate work is a name and two dates.

Two habits from apps/home/admin.py are deliberately NOT carried over:
  * ``list_editable`` -- a certificate must never be mutable from a list view.
  * deletion -- these are records of an award. Revoke, never delete.
"""

from __future__ import annotations

import csv
import io
import zipfile

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from . import qr
from .models import (
    Certificate,
    CertificateAuditEvent,
    CertificateScan,
    Cohort,
    SerialSequence,
)

STATUS_COLOURS = {
    'draft': '#6b7280',
    'issued': '#006377',
    'revoked': '#b91c1c',
    'superseded': '#b45309',
}


def _absolute(request, path_):
    return request.build_absolute_uri(path_)


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'program_title', 'year',
        'certificate_count', 'issue_link', 'is_active',
    )
    list_filter = ('year', 'is_active', 'program_type_label')
    search_fields = ('name', 'code', 'program_title')
    ordering = ('-year', 'name')
    fieldsets = (
        ('Identity', {'fields': ('name', 'code', 'year', 'is_active')}),
        ('Programme', {
            'fields': (
                'program_title', 'program_type_label', 'program_slug',
                'credential_title', 'duration_text', 'format', 'venue',
            ),
        }),
        ('Default dates', {
            'fields': (
                'start_date', 'end_date',
                'default_completion_date', 'default_issue_date',
            ),
            'description': 'Used to pre-fill new certificates in this cohort.',
        }),
        ('Signatories', {
            'fields': (
                'signatory_1_name', 'signatory_1_title',
                'signatory_2_name', 'signatory_2_title',
            ),
        }),
    )

    @admin.display(description='Certificates')
    def certificate_count(self, obj):
        count = obj.certificates.count()
        if not count:
            return '0'
        url = reverse('admin:credentials_certificate_changelist')
        return format_html('<a href="{}?cohort__id__exact={}">{}</a>', url, obj.pk, count)

    @admin.display(description='')
    def issue_link(self, obj):
        url = reverse('admin:credentials_certificate_add')
        return format_html('<a class="button" href="{}?cohort={}">Issue certificate</a>', url, obj.pk)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'serial', 'recipient_full_name', 'program_title', 'cohort',
        'issue_date', 'status_badge', 'scan_count', 'last_scanned_at',
    )
    list_filter = ('status', 'cohort', 'program_type_label', ('issue_date', admin.DateFieldListFilter))
    search_fields = ('serial', 'recipient_full_name', 'recipient_email', 'token', 'program_title')
    date_hierarchy = 'issue_date'
    ordering = ('-issue_date', '-id')
    list_select_related = ('cohort',)
    autocomplete_fields = ('superseded_by',)
    actions = ('mark_as_issued', 'revoke_selected', 'download_qr_pack', 'export_merge_csv')

    # Always read-only. The frozen credential fields are added by
    # get_readonly_fields() once the certificate leaves draft.
    base_readonly = (
        'token_display_field', 'verify_url_display', 'qr_preview', 'recent_scans',
        'created_at', 'updated_at', 'issued_by', 'issued_at',
        'scan_count', 'first_scanned_at', 'last_scanned_at',
        'pdf_sha256', 'pdf_size',
    )

    fieldsets = (
        ('Recipient', {
            'fields': ('recipient_full_name', 'recipient_email', 'recipient_country'),
        }),
        # Second on purpose: after saving, the QR and copyable URL are visible
        # without scrolling, which is what the registrar needs next.
        ('Verification', {
            'fields': ('serial', 'token_display_field', 'verify_url_display', 'qr_preview'),
        }),
        ('Credential', {
            'fields': (
                'cohort', 'program_title', 'program_type_label', 'program_slug',
                'credential_title', 'duration_text', 'format', 'venue',
                'signatory_1_name', 'signatory_1_title',
                'signatory_2_name', 'signatory_2_title',
            ),
        }),
        ('Dates', {'fields': ('completion_date', 'issue_date', 'expires_on')}),
        ('Status', {'fields': ('status', 'superseded_by')}),
        ('Archived document', {
            'classes': ('collapse',),
            'fields': ('pdf', 'pdf_sha256', 'pdf_size'),
            'description': (
                'Private archival copy. Stored on a non-public bucket and never '
                'linked from the public verification page.'
            ),
        }),
        ('Revocation', {
            'classes': ('collapse',),
            'fields': ('revoked_at', 'revoked_by', 'revocation_reason', 'revocation_public_note'),
        }),
        ('Internal', {
            'classes': ('collapse',),
            'fields': ('notes', 'issued_by', 'issued_at', 'created_at', 'updated_at',
                       'scan_count', 'first_scanned_at', 'last_scanned_at', 'recent_scans'),
        }),
    )

    # -- Permissions -------------------------------------------------------
    def has_delete_permission(self, request, obj=None):
        # A certificate is a record of an award. Revoke it; do not erase it.
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.base_readonly)
        if obj and obj.status != Certificate.Status.DRAFT:
            from .models import FROZEN_FIELDS
            readonly += [f for f in FROZEN_FIELDS if f != 'token']
        return tuple(dict.fromkeys(readonly))

    def get_changeform_initial_data(self, request):
        """Pre-fill from ?cohort=<id>, as linked from the cohort changelist."""
        initial = super().get_changeform_initial_data(request)
        cohort_id = request.GET.get('cohort')
        if not cohort_id:
            return initial
        cohort = Cohort.objects.filter(pk=cohort_id).first()
        if not cohort:
            return initial
        initial.update({
            'cohort': cohort.pk,
            'program_title': cohort.program_title,
            'program_type_label': cohort.program_type_label,
            'program_slug': cohort.program_slug,
            'credential_title': cohort.credential_title,
            'duration_text': cohort.duration_text,
            'format': cohort.format,
            'venue': cohort.venue,
            'signatory_1_name': cohort.signatory_1_name,
            'signatory_1_title': cohort.signatory_1_title,
            'signatory_2_name': cohort.signatory_2_name,
            'signatory_2_title': cohort.signatory_2_title,
            'completion_date': cohort.default_completion_date,
            'issue_date': cohort.default_issue_date or timezone.localdate(),
        })
        return initial

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.issued_by = request.user
        if obj.status == Certificate.Status.ISSUED and obj.issued_at is None:
            obj.issued_at = timezone.now()
        super().save_model(request, obj, form, change)
        CertificateAuditEvent.objects.create(
            certificate=obj,
            actor=request.user,
            action=(CertificateAuditEvent.Action.EDITED if change
                    else CertificateAuditEvent.Action.CREATED),
            changes={'fields': list(form.changed_data)},
        )

    # -- Display helpers ---------------------------------------------------
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:700;">{}</span>',
            STATUS_COLOURS.get(obj.status, '#6b7280'), obj.get_status_display(),
        )

    @admin.display(description='Verification code')
    def token_display_field(self, obj):
        if not obj or not obj.token:
            return '— generated on save —'
        return format_html('<code style="font-size:15px;letter-spacing:1px;">{}</code>', obj.token_display)

    @admin.display(description='Verify URL')
    def verify_url_display(self, obj):
        if not obj or not obj.token:
            return '— generated on save —'
        url = obj.get_absolute_url()
        return format_html(
            '<input type="text" readonly value="{}" style="width:32em;padding:4px;" '
            'onclick="this.select();document.execCommand(\'copy\');">'
            ' <a href="{}" target="_blank" rel="noopener">open</a>',
            url, url,
        )

    @admin.display(description='QR code')
    def qr_preview(self, obj):
        """Rendered inline as a data URI. Never written to storage.

        Generated QR images are derived data; persisting them would put every
        certificate's QR on a world-readable, year-cached media URL for no gain.
        """
        if not obj or not obj.token:
            return '— generated on save —'
        payload = qr.build_payload('https://idi.africa', obj.get_short_url())
        svg_url = reverse('admin:credentials_certificate_qr_svg', args=[obj.pk])
        png_url = reverse('admin:credentials_certificate_qr_png', args=[obj.pk])
        return format_html(
            '<div><img src="{}" width="170" height="170" alt="QR code for {}">'
            '<p style="margin:6px 0 0;font-size:11px;color:#555;">Encodes: <code>{}</code></p>'
            '<p style="margin:4px 0 0;"><a class="button" href="{}">Download SVG (print)</a> '
            '<a class="button" href="{}">PNG</a></p>'
            '<p style="margin:6px 0 0;font-size:11px;color:#b45309;">'
            'Print at {}mm minimum ({}mm preferred), keep the white margin.</p></div>',
            qr.data_uri(payload), obj.serial, payload, svg_url, png_url,
            qr.MIN_PRINT_MM, qr.RECOMMENDED_PRINT_MM,
        )

    @admin.display(description='Recent scans')
    def recent_scans(self, obj):
        """Last ten only, as static HTML.

        Deliberately not an inline: inlines do not paginate, so a widely-shared
        certificate would render hundreds of forms on this page.
        """
        if not obj or not obj.pk:
            return '—'
        rows = obj.scans.all()[:10]
        if not rows:
            return 'No scans recorded yet.'
        body = format_html_join(
            '', '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>',
            ((s.scanned_at.strftime('%Y-%m-%d %H:%M'), s.get_outcome_display(),
              s.ua_family, 'bot' if s.is_bot else 'person', s.hit_count) for s in rows),
        )
        url = reverse('admin:credentials_certificatescan_changelist')
        return format_html(
            '<table style="font-size:12px;"><tr><th>When</th><th>Outcome</th>'
            '<th>Client</th><th>Type</th><th>Hits</th></tr>{}</table>'
            '<p style="margin-top:6px;"><a href="{}?certificate__id__exact={}">View all scans</a></p>',
            body, url, obj.pk,
        )

    # -- Custom admin views ------------------------------------------------
    def get_urls(self):
        custom = [
            path('<int:pk>/qr.svg', self.admin_site.admin_view(self.qr_svg_view),
                 name='credentials_certificate_qr_svg'),
            path('<int:pk>/qr.png', self.admin_site.admin_view(self.qr_png_view),
                 name='credentials_certificate_qr_png'),
        ]
        return custom + super().get_urls()

    def _payload_for(self, request, pk):
        certificate = get_object_or_404(Certificate, pk=pk)
        if not request.user.has_perm('credentials.view_certificate'):
            raise PermissionDenied
        return certificate, qr.build_payload(
            f'{request.scheme}://{request.get_host()}', certificate.get_short_url()
        )

    def qr_svg_view(self, request, pk):
        certificate, payload = self._payload_for(request, pk)
        response = HttpResponse(qr.svg_bytes(payload), content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="{certificate.serial}.svg"'
        return response

    def qr_png_view(self, request, pk):
        certificate, payload = self._payload_for(request, pk)
        response = HttpResponse(qr.png_bytes(payload), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{certificate.serial}.png"'
        return response

    # -- Actions -----------------------------------------------------------
    @admin.action(description='Mark selected as issued')
    def mark_as_issued(self, request, queryset):
        issued = 0
        for certificate in queryset.filter(status=Certificate.Status.DRAFT):
            missing = [f for f in ('program_title', 'credential_title') if not getattr(certificate, f)]
            if missing:
                self.message_user(
                    request,
                    f'{certificate.serial}: cannot issue, missing {", ".join(missing)}.',
                    level=messages.ERROR,
                )
                continue
            certificate.status = Certificate.Status.ISSUED
            certificate.issued_at = timezone.now()
            certificate.issued_by = certificate.issued_by or request.user
            certificate.save()
            CertificateAuditEvent.objects.create(
                certificate=certificate, actor=request.user,
                action=CertificateAuditEvent.Action.ISSUED,
            )
            issued += 1
        self.message_user(request, f'{issued} certificate(s) issued.', level=messages.SUCCESS)

    @admin.action(description='Revoke selected…')
    def revoke_selected(self, request, queryset):
        """Two-step, requiring a reason. Never a one-click destructive action."""
        if request.POST.get('confirm_revoke'):
            reason = request.POST.get('reason', '').strip()
            public_note = request.POST.get('public_note', '').strip()
            if not reason:
                self.message_user(request, 'A reason is required to revoke.', level=messages.ERROR)
            else:
                now = timezone.now()
                count = 0
                for certificate in queryset.exclude(status=Certificate.Status.REVOKED):
                    certificate.status = Certificate.Status.REVOKED
                    certificate.revoked_at = now
                    certificate.revoked_by = request.user
                    certificate.revocation_reason = reason
                    certificate.revocation_public_note = public_note
                    certificate.save()
                    CertificateAuditEvent.objects.create(
                        certificate=certificate, actor=request.user,
                        action=CertificateAuditEvent.Action.REVOKED,
                        changes={'reason': reason},
                    )
                    count += 1
                self.message_user(request, f'{count} certificate(s) revoked.', level=messages.WARNING)
                return None
        return render(request, 'admin/credentials/revoke_confirm.html', {
            'certificates': queryset,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
        })

    @admin.action(description='Download QR pack (ZIP)')
    def download_qr_pack(self, request, queryset):
        buffer = io.BytesIO()
        base = f'{request.scheme}://{request.get_host()}'
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for certificate in queryset:
                payload = qr.build_payload(base, certificate.get_short_url())
                archive.writestr(f'{certificate.serial}.svg', qr.svg_bytes(payload))
        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="dida-qr-pack.zip"'
        return response

    @admin.action(description='Export merge CSV (for certificate artwork)')
    def export_merge_csv(self, request, queryset):
        """The bridge from Django to the design tool.

        Drives InDesign Data Merge and the Figma/Illustrator variable-data
        plugins. Deliberately excludes recipient_email.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dida-certificates.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'serial', 'recipient_full_name', 'program_title', 'credential_title',
            'completion_date', 'issue_date', 'venue',
            'signatory_1_name', 'signatory_1_title',
            'signatory_2_name', 'signatory_2_title',
            'verification_code', 'verify_url', 'qr_payload', 'qr_filename',
        ])
        base = f'{request.scheme}://{request.get_host()}'
        for c in queryset.select_related('cohort'):
            writer.writerow([
                c.serial, c.recipient_full_name, c.program_title, c.credential_title,
                c.completion_date, c.issue_date, c.venue,
                c.signatory_1_name, c.signatory_1_title,
                c.signatory_2_name, c.signatory_2_title,
                c.token_display, _absolute(request, c.get_absolute_url()),
                qr.build_payload(base, c.get_short_url()), f'{c.serial}.svg',
            ])
        return response


@admin.register(CertificateScan)
class CertificateScanAdmin(admin.ModelAdmin):
    """Read-only. Rows are written by the verification view, never by hand."""

    list_display = (
        'scanned_at', 'certificate', 'certificate_serial', 'outcome',
        'lookup_method', 'ua_family', 'is_bot', 'hit_count',
    )
    list_filter = ('outcome', 'is_bot', 'lookup_method', 'scanned_at')
    search_fields = ('certificate_serial',)
    date_hierarchy = 'scanned_at'
    list_select_related = ('certificate',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(CertificateAuditEvent)
class CertificateAuditEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'certificate', 'action', 'actor')
    list_filter = ('action', 'created_at')
    search_fields = ('certificate__serial',)
    date_hierarchy = 'created_at'
    list_select_related = ('certificate', 'actor')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SerialSequence)
class SerialSequenceAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'year', 'last_number')

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
