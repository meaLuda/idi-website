"""Contact-form tests.

The view previously accepted a POST, set success = True and discarded the data,
so a visitor saw "Message Sent!" while the enquiry was lost. These tests pin the
behaviour that must never regress: the enquiry is stored, and it is stored even
when notification email fails.
"""

from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.home.models import ContactMessage

VALID = {
    'name': 'Ada Kimani',
    'organization': 'Ministry of Health',
    'email': 'ada@example.com',
    'inquiry_type': 'academy-fellowship',
    'message': 'We would like to discuss a cohort for our analysts.',
    'website': '',
    'ts': '',
}


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CONTACT_NOTIFICATION_EMAILS=['collectives@idi.africa'],
)
class ContactSubmissionTests(TestCase):
    def setUp(self):
        self.url = reverse('home:contact')

    def test_a_valid_submission_is_persisted(self):
        """The regression that matters: the enquiry must actually be stored."""
        self.client.post(self.url, VALID)
        message = ContactMessage.objects.get()
        self.assertEqual(message.name, 'Ada Kimani')
        self.assertEqual(message.email, 'ada@example.com')
        self.assertEqual(message.organization, 'Ministry of Health')
        self.assertEqual(message.inquiry_type, 'academy-fellowship')
        self.assertIn('cohort for our analysts', message.message)

    def test_it_redirects_after_posting(self):
        """Post/Redirect/Get, so refreshing cannot resubmit the enquiry."""
        response = self.client.post(self.url, VALID)
        self.assertEqual(response.status_code, 302)
        self.assertIn('sent=1', response['Location'])

    def test_the_success_state_is_shown_after_the_redirect(self):
        response = self.client.get(self.url, {'sent': '1'})
        self.assertContains(response, 'Message Sent')

    def test_staff_are_notified(self):
        self.client.post(self.url, VALID)
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn('ada@example.com', body)
        self.assertIn('Ministry of Health', body)
        self.assertEqual(mail.outbox[0].to, ['collectives@idi.africa'])
        self.assertTrue(ContactMessage.objects.get().notification_sent)

    def test_the_enquiry_survives_a_mail_failure(self):
        """A broken mail server must not lose a business lead."""
        with mock.patch('apps.home.views.send_mail', side_effect=OSError('smtp down')):
            response = self.client.post(self.url, VALID)
        self.assertEqual(response.status_code, 302)
        message = ContactMessage.objects.get()
        self.assertEqual(message.name, 'Ada Kimani')
        self.assertFalse(message.notification_sent)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ContactValidationTests(TestCase):
    def setUp(self):
        self.url = reverse('home:contact')

    def test_invalid_email_is_rejected_and_nothing_is_stored(self):
        response = self.client.post(self.url, {**VALID, 'email': 'not-an-email'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, 'Please check the form below')

    def test_a_missing_message_is_rejected(self):
        self.client.post(self.url, {**VALID, 'message': ''})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_a_trivially_short_message_is_rejected(self):
        self.client.post(self.url, {**VALID, 'message': 'hi'})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_the_honeypot_blocks_bots(self):
        self.client.post(self.url, {**VALID, 'website': 'http://spam.example'})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_submitted_values_survive_a_validation_error(self):
        """A visitor must not have to retype everything."""
        response = self.client.post(self.url, {**VALID, 'email': 'nope'})
        self.assertContains(response, 'Ada Kimani')
        self.assertContains(response, 'cohort for our analysts')

    def test_no_enquiry_is_created_on_a_plain_get(self):
        self.client.get(self.url)
        self.assertEqual(ContactMessage.objects.count(), 0)
