"""Forms for apps.home.

The project had no forms.py at all; the contact view read request.POST only to
decide it had been posted to, and threw the data away.
"""

from __future__ import annotations

import time

from django import forms
from django.core import signing

from .models import ContactMessage

MIN_FILL_SECONDS = 2.0
TIMESTAMP_SALT = 'home.contact'


class ContactForm(forms.ModelForm):
    """Validates and persists a contact enquiry.

    Field names match the existing markup in templates/home/contact.html
    (name / org / email / inquiry_type / message) so the template keeps working.
    """

    # Honeypot. Hidden from people; naive bots fill every field they find.
    website = forms.CharField(required=False, widget=forms.HiddenInput())
    ts = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'inquiry_type', 'message')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The template posts the organisation as "org".
        self.fields['organization'] = forms.CharField(max_length=160, required=False)
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['message'].required = True

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
            rendered_at = signing.loads(raw, salt=TIMESTAMP_SALT, max_age=7200)
        except signing.BadSignature:
            raise forms.ValidationError('Invalid submission.')
        if time.time() - float(rendered_at) < MIN_FILL_SECONDS:
            raise forms.ValidationError('That was submitted too quickly. Please try again.')
        return raw

    def clean_message(self):
        message = (self.cleaned_data.get('message') or '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Please give us a little more detail.')
        return message

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.organization = self.cleaned_data.get('organization', '')
        if commit:
            instance.save()
        return instance
