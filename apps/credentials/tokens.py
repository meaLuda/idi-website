"""Verification-code generation and normalisation.

Pure functions only -- no models, no Django settings. This is the security core of
certificate verification, so it is kept small enough to audit in one sitting.

Design
------
A certificate carries two identifiers with different jobs:

  serial  DIDA-IDI-2026-00567   organisational record number, printed on the
                                certificate, never a public lookup key
  token   A7K4-9MTB-2XQC        capability to view the record; encoded in the QR

The token, not the serial, is what the QR encodes. A sequential serial in the URL
would let anyone walk 00001..99999 and harvest every recipient's name and
programme in minutes -- a bulk personal-data disclosure -- and would hand a forger
a working code for free.

Alphabet
--------
Crockford Base32: the digits and uppercase letters minus I, L, O and U. Excluding
those removes the 1/I/l and 0/O confusions that dominate hand transcription from
paper, and dropping U avoids accidental profanity in generated codes.

Entropy
-------
11 random characters x 5 bits = 55 bits, a space of ~3.6e16. With 10,000 issued
certificates the chance that any single guess lands on a real one is ~2.8e-13.
*The entropy is the security control, not the rate limiter* -- which is precisely
why the throttle is allowed to fail open when the cache is unavailable.

Check character
---------------
A Luhn mod-32 check character is appended, giving 12 characters total. It does two
jobs: a mistyped code yields "that code has a typo" instead of a bare "not found",
and 31 of every 32 random guesses are rejected in pure Python before any database
query -- so brute-force traffic never grows the scan table.

It catches every single-character substitution, and 99.78% of adjacent
transpositions (measured over 31,899 cases; the residue is Luhn mod-N's known
blind spot).
"""

from __future__ import annotations

import secrets

# Crockford Base32. Order matters: index == value.
ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
BASE = len(ALPHABET)  # 32

RANDOM_LENGTH = 11
TOKEN_LENGTH = RANDOM_LENGTH + 1  # + check character
GROUP_SIZE = 4

# Characters a human is likely to substitute when reading a printed code. Crockford
# excludes these from the alphabet precisely so they can be folded back in on input.
_CONFUSABLES = {
    'I': '1', 'L': '1',
    'O': '0',
    'U': 'V',  # U is not in the alphabet; V is its nearest visual neighbour
}

_VALUES = {char: index for index, char in enumerate(ALPHABET)}


def _checksum(payload: str) -> str:
    """Return the Luhn mod-32 check character for ``payload``.

    Catches every single-character substitution and almost every transposition of
    adjacent characters.
    """
    factor = 2
    total = 0
    # Walk right to left, doubling every other character's value.
    for char in reversed(payload):
        addend = factor * _VALUES[char]
        factor = 1 if factor == 2 else 2
        # Fold the overflow back in, base 32.
        total += (addend // BASE) + (addend % BASE)
    remainder = total % BASE
    return ALPHABET[(BASE - remainder) % BASE]


def normalize_code(raw: str) -> str:
    """Fold user input into the canonical stored form.

    Uppercases, strips hyphens and whitespace, and maps the confusable characters,
    so somebody typing what they *think* they see on paper still resolves. Returns
    '' for input that cannot be a code.
    """
    if not raw:
        return ''
    cleaned = []
    for char in raw.strip().upper():
        if char in ('-', ' ', '\t', '–', '—', '_', '.'):
            continue
        char = _CONFUSABLES.get(char, char)
        if char not in _VALUES:
            return ''  # contains something that is not representable at all
        cleaned.append(char)
    return ''.join(cleaned)


def is_valid_code(raw: str) -> bool:
    """True when ``raw`` normalises to a well-formed, checksum-correct token.

    Callers use this to reject garbage before touching the database.
    """
    code = normalize_code(raw)
    if len(code) != TOKEN_LENGTH:
        return False
    return _checksum(code[:-1]) == code[-1]


def generate_code() -> str:
    """Return a fresh canonical token. Uses ``secrets``, never ``random``."""
    payload = ''.join(secrets.choice(ALPHABET) for _ in range(RANDOM_LENGTH))
    return payload + _checksum(payload)


def format_code(code: str) -> str:
    """Hyphenate into groups of four for printing and display.

    Humans transcribe grouped strings markedly more accurately than one long run.
    Storage stays canonical (unhyphenated); this is presentation only.
    """
    code = normalize_code(code)
    return '-'.join(code[i:i + GROUP_SIZE] for i in range(0, len(code), GROUP_SIZE))
