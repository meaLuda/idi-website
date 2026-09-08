"""Manual certificate lookup form.

The first real Form in this project. Hardened without a CAPTCHA: a honeypot field
plus a signed render timestamp stops naive bots at no accessibility cost.
"""

from __future__ import annotations

import time

from django import forms
from django.core import signing

from .tokens import TOKEN_LENGTH, is_valid_code, normalize_code

# Submissions faster than this are not human.
MIN_FILL_SECONDS = 1.5
TIMESTAMP_SALT = 'credentials.lookup'


class CertificateLookupForm(forms.Form):
    code = forms.CharField(
        label='Verification code',
        max_length=32,
        strip=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'A7K4-9MTB-2XQC',
            'autocomplete': 'off',
            'autocapitalize': 'characters',
            'spellcheck': 'false',
            'inputmode': 'latin',
            'aria-describedby': 'code-help',
        }),
        help_text='The code printed beneath the QR code on the certificate.',
    )
    # Honeypot: hidden from people, irresistible to naive bots. Named plausibly
    # because bots skip fields called "honeypot".
    website = forms.CharField(required=False, widget=forms.HiddenInput())
    ts = forms.CharField(required=False, widget=forms.HiddenInput())

    @staticmethod
    def make_timestamp():
        return signing.dumps(time.time(), salt=TIMESTAMP_SALT)

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Invalid submission.')
        return ''

    def clean_ts(self):
        raw = self.cleaned_data.get('ts') or ''
        if not raw:
            return ''
        try:
            rendered_at = signing.loads(raw, salt=TIMESTAMP_SALT, max_age=3600)
        except signing.BadSignature:
            raise forms.ValidationError('Invalid submission.')
        if time.time() - float(rendered_at) < MIN_FILL_SECONDS:
            raise forms.ValidationError('That was too quick — please try again.')
        return raw

    def clean_code(self):
        raw = self.cleaned_data['code']
        code = normalize_code(raw)
        if len(code) != TOKEN_LENGTH or not is_valid_code(code):
            # One message for every failure mode, so the form never confirms that
            # a partially-correct code exists.
            raise forms.ValidationError(
                "That doesn't look like a valid verification code. "
                'Please check the code printed on the certificate and try again.'
            )
        return code
