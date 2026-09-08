"""QR code generation for printed certificates.

Uses ``segno``: zero dependencies (no Dockerfile change), native compact
path-based SVG with real physical units, and a one-call data URI for the admin
preview so nothing is ever written to disk.

Payload optimisation
--------------------
QR alphanumeric mode encodes 0-9, A-Z and a few symbols at ~5.5 bits per
character, but it has no lowercase -- a single lowercase character forces the
whole symbol into 8-bit byte mode and costs a version.

    https://idi.africa/v/a7k49mtb2xqc   lowercase, byte mode  -> version 4 (41 modules)
    HTTPS://IDI.AFRICA/V/A7K49MTB2XQC   uppercase, alnum mode -> version 3 (37 modules)

(Measured, not estimated -- see tests/test_qr.py, which asserts the mode and
version so a future payload change cannot silently inflate the symbol.)

Hostnames are case-insensitive per RFC 3986, and the path matches
case-insensitively because lookup normalises the code. So the QR carries the
uppercase, hyphen-free form while the certificate prints the friendly lowercase
URL and the hyphenated code as text.

Error correction level H (30%) is deliberate: a printed certificate gets folded,
framed behind glass, stamped with a seal, signed across, photocopied and
photographed at an angle in bad light.
"""

from __future__ import annotations

import io

import segno

# 4 modules of quiet zone on every side. segno's default; never set this to 0.
QUIET_ZONE = 4

# Minimum printed size. The symbol is version 3: 29 modules + 8 of quiet zone =
# 37 across. Phone cameras need roughly 0.4mm per module, putting the hard floor
# at 37 x 0.4 = 14.8mm -- so 15mm is the true minimum and 20mm (0.54mm modules)
# is the comfortable one. The ~10mm in the original certificate mockup would give
# 0.27mm modules and scan unreliably.
MIN_PRINT_MM = 15
RECOMMENDED_PRINT_MM = 20
MODULES_ACROSS = 37


def build_payload(base_url, path):
    """Return the uppercase, hyphen-free URL to encode."""
    return f'{base_url.rstrip("/")}{path}'.upper()


def make_qr(payload):
    """Return a segno QR object at error-correction level H."""
    return segno.make(payload, error='h', micro=False)


def svg_bytes(payload, scale_mm=RECOMMENDED_PRINT_MM):
    """Return print-ready SVG sized in real millimetres.

    Vector output is what a designer actually needs: it RIPs cleanly and places
    into InDesign, Illustrator, Figma or Affinity at any size.
    """
    qr = make_qr(payload)
    buf = io.BytesIO()
    # unit='mm' makes the symbol physically sized rather than pixel sized.
    qr.save(
        buf, kind='svg', unit='mm',
        scale=scale_mm / (qr.symbol_size(border=QUIET_ZONE)[0]),
        border=QUIET_ZONE, dark='#000000', light='#ffffff',
    )
    return buf.getvalue()


def png_bytes(payload, dpi=1200, size_mm=RECOMMENDED_PRINT_MM):
    """Return a high-resolution PNG fallback for tools that mangle SVG."""
    qr = make_qr(payload)
    modules = qr.symbol_size(border=QUIET_ZONE)[0]
    target_px = int((size_mm / 25.4) * dpi)
    scale = max(1, round(target_px / modules))
    buf = io.BytesIO()
    qr.save(buf, kind='png', scale=scale, border=QUIET_ZONE, dpi=dpi)
    return buf.getvalue()


def data_uri(payload, scale=6):
    """Inline SVG data URI for the admin preview -- nothing written to storage.

    Generated QR images are derived data. Persisting them to the media bucket
    would put them on a world-readable, year-cached URL for no benefit.
    """
    return make_qr(payload).svg_data_uri(scale=scale, border=QUIET_ZONE)
