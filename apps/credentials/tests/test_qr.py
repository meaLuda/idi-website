"""QR tests.

These pin the payload encoding, because a change that silently pushes the symbol
to a higher version makes every already-printed certificate's size guidance wrong.
"""

from django.test import SimpleTestCase

from apps.credentials import qr, tokens


class PayloadTests(SimpleTestCase):
    def setUp(self):
        self.code = tokens.generate_code()
        self.payload = qr.build_payload('https://idi.africa', f'/v/{self.code}')

    def test_payload_is_uppercase_and_unhyphenated(self):
        self.assertEqual(self.payload, self.payload.upper())
        self.assertNotIn('-', self.payload.replace('HTTPS://', ''))
        self.assertTrue(self.payload.startswith('HTTPS://IDI.AFRICA/V/'))

    def test_payload_stays_in_alphanumeric_mode(self):
        """Lowercase would force byte mode and cost a version."""
        self.assertEqual(qr.make_qr(self.payload).mode, 'alphanumeric')

    def test_error_correction_is_level_h(self):
        self.assertEqual(qr.make_qr(self.payload).error.upper(), 'H')

    def test_symbol_does_not_exceed_version_3(self):
        symbol = qr.make_qr(self.payload)
        self.assertLessEqual(
            symbol.version, 3,
            'payload grew past version 3; printed size guidance must be revisited',
        )
        self.assertEqual(symbol.symbol_size(border=qr.QUIET_ZONE)[0], qr.MODULES_ACROSS)

    def test_minimum_print_size_keeps_modules_scannable(self):
        """15mm must still yield >= 0.4mm modules, the phone-camera floor."""
        module_mm = qr.MIN_PRINT_MM / qr.MODULES_ACROSS
        self.assertGreaterEqual(round(module_mm, 3), 0.4)


class OutputTests(SimpleTestCase):
    def setUp(self):
        self.payload = qr.build_payload(
            'https://idi.africa', f'/v/{tokens.generate_code()}'
        )

    def test_svg_is_vector_and_non_empty(self):
        svg = qr.svg_bytes(self.payload).decode()
        self.assertIn('<svg', svg)
        self.assertIn('mm', svg, 'SVG should carry physical units for print')

    def test_png_is_a_png(self):
        self.assertTrue(qr.png_bytes(self.payload).startswith(b'\x89PNG\r\n\x1a\n'))

    def test_data_uri_is_inline_svg(self):
        self.assertTrue(qr.data_uri(self.payload).startswith('data:image/svg+xml'))

    def test_quiet_zone_is_never_dropped(self):
        self.assertEqual(qr.QUIET_ZONE, 4)
