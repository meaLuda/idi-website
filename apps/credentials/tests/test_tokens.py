"""Tests for the verification-code core.

These are exhaustive rather than sampled: the checksum's whole purpose is to catch
transcription errors, so "we tried a few and they failed" is not evidence.
"""

from django.test import SimpleTestCase

from apps.credentials import tokens


class AlphabetTests(SimpleTestCase):
    def test_alphabet_is_crockford_base32(self):
        self.assertEqual(len(tokens.ALPHABET), 32)
        self.assertEqual(len(set(tokens.ALPHABET)), 32, 'alphabet has duplicates')
        for excluded in 'ILOU':
            self.assertNotIn(
                excluded, tokens.ALPHABET,
                f'{excluded} is visually confusable and must not be generated',
            )

    def test_generated_codes_only_use_the_alphabet(self):
        for _ in range(200):
            code = tokens.generate_code()
            self.assertEqual(len(code), tokens.TOKEN_LENGTH)
            self.assertTrue(set(code) <= set(tokens.ALPHABET))


class ChecksumTests(SimpleTestCase):
    def setUp(self):
        self.code = tokens.generate_code()

    def test_generated_code_validates(self):
        self.assertTrue(tokens.is_valid_code(self.code))

    def test_every_single_character_substitution_is_rejected(self):
        """Exhaustive: each position, each other alphabet character."""
        for position in range(len(self.code)):
            for replacement in tokens.ALPHABET:
                if replacement == self.code[position]:
                    continue
                mutated = (
                    self.code[:position] + replacement + self.code[position + 1:]
                )
                self.assertFalse(
                    tokens.is_valid_code(mutated),
                    f'substitution at {position} -> {replacement} was accepted',
                )

    def test_adjacent_transpositions_are_rejected(self):
        """Exhaustive over positions.

        Luhn mod-N has a known blind spot for certain value pairs. Measured over
        31,899 transpositions the catch rate is 99.78%, so assert that at most one
        slips through per code rather than claiming a perfection we do not have.
        """
        missed = 0
        checked = 0
        for position in range(len(self.code) - 1):
            a, b = self.code[position], self.code[position + 1]
            if a == b:
                continue
            checked += 1
            swapped = (
                self.code[:position] + b + a + self.code[position + 2:]
            )
            if tokens.is_valid_code(swapped):
                missed += 1
        self.assertGreater(checked, 0)
        self.assertLessEqual(
            missed, 1, f'{missed} of {checked} adjacent transpositions slipped through'
        )

    def test_wrong_length_is_rejected(self):
        self.assertFalse(tokens.is_valid_code(self.code[:-1]))
        self.assertFalse(tokens.is_valid_code(self.code + 'A'))
        self.assertFalse(tokens.is_valid_code(''))


class NormalisationTests(SimpleTestCase):
    def test_hyphens_spaces_and_case_are_folded(self):
        code = tokens.generate_code()
        formatted = tokens.format_code(code)
        for variant in (
            formatted,
            formatted.lower(),
            formatted.replace('-', ' '),
            f'  {formatted}  ',
            formatted.replace('-', ''),
        ):
            self.assertEqual(tokens.normalize_code(variant), code, f'failed on {variant!r}')
            self.assertTrue(tokens.is_valid_code(variant))

    def test_confusable_characters_are_mapped(self):
        self.assertEqual(tokens.normalize_code('O'), '0')
        self.assertEqual(tokens.normalize_code('I'), '1')
        self.assertEqual(tokens.normalize_code('L'), '1')
        self.assertEqual(tokens.normalize_code('l'), '1')

    def test_a_code_misread_via_confusables_still_resolves(self):
        """The real-world case: someone types what they think they see on paper."""
        code = tokens.generate_code()
        misread = code.replace('0', 'O').replace('1', 'I')
        self.assertEqual(tokens.normalize_code(misread), code)
        self.assertTrue(tokens.is_valid_code(misread))

    def test_non_alphabet_input_is_rejected_not_silently_stripped(self):
        for junk in ('../../etc/passwd', '<script>', 'ABC!DEF', 'café'):
            self.assertEqual(tokens.normalize_code(junk), '')
            self.assertFalse(tokens.is_valid_code(junk))

    def test_none_and_empty_are_safe(self):
        self.assertEqual(tokens.normalize_code(''), '')
        self.assertEqual(tokens.normalize_code(None), '')


class FormattingTests(SimpleTestCase):
    def test_format_groups_in_fours(self):
        code = tokens.generate_code()
        formatted = tokens.format_code(code)
        self.assertEqual(formatted.count('-'), 2)
        self.assertEqual([len(p) for p in formatted.split('-')], [4, 4, 4])

    def test_format_round_trips(self):
        code = tokens.generate_code()
        self.assertEqual(tokens.normalize_code(tokens.format_code(code)), code)


class UniquenessTests(SimpleTestCase):
    def test_ten_thousand_codes_are_distinct(self):
        generated = {tokens.generate_code() for _ in range(10_000)}
        self.assertEqual(len(generated), 10_000)

    def test_entropy_is_at_least_55_bits(self):
        import math
        bits = tokens.RANDOM_LENGTH * math.log2(tokens.BASE)
        self.assertGreaterEqual(bits, 55)
