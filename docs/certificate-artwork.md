# DIDA certificate artwork — QR and verification spec

For the designer. Everything below is required for the QR code to scan reliably
and for the verification link to work.

## What changes from the current mockup

| # | Change | Why |
|---|---|---|
| 1 | **QR encodes a new URL** (see below) | The mockup points at `credentials.dida-idi.org`; verification lives on `idi.africa` |
| 2 | **Add one text field under the QR** | The code must be typeable when a QR reader isn't available |
| 3 | **QR must be at least 15 mm square** | The mockup's ~10 mm is below the reliable scanning threshold |
| 4 | Relabel the serial as `Certificate No.` | It is a record number, not the verification key |
| 5 | Fix the mockup's own mismatch | Caption reads `…-0001`, serial reads `…-00567` |

## The QR code

**Encodes exactly this**, uppercase, no hyphens:

```
HTTPS://IDI.AFRICA/V/A7K49MTB2XQC
```

Do not retype this by hand. Export it from the admin — every certificate has a
**Download SVG (print)** button, and there is a bulk **Download QR pack (ZIP)**
action for a whole cohort.

Uppercase is deliberate: it keeps the symbol in QR "alphanumeric" mode. Lowercase
forces a larger symbol that needs ~1.6 mm more space to scan.

### Non-negotiable

| Property | Value |
|---|---|
| Minimum size | **15 mm × 15 mm** |
| Preferred size | **20 mm × 20 mm** |
| Quiet zone | **4 modules of clear white on all four sides** — do not crop |
| Colour | Black, or IDI teal `#006377`, on white |
| Never | Brand orange `#f99a00` (too little contrast), inverted, gradients, or a logo over the centre |
| Never | Place it on the teal footer band or overlap the gold seal |

The symbol is 37 modules across including its quiet zone. At 15 mm each module is
0.405 mm — right at the limit phone cameras can resolve. At 20 mm it is 0.54 mm,
which scans comfortably at arm's length. Below 15 mm it will fail in poor light
and at an angle, which is exactly how certificates get scanned in practice.

## Text beneath the QR

Add this block, centred under the QR:

```
Verification code
A7K4-9MTB-2XQC
Verify at idi.africa/verify
```

* The code in **monospace or a wide-tracked face, minimum 8 pt**.
* Keep the hyphens in the printed text — people transcribe grouped characters far
  more accurately. (The hyphens are *not* in the QR itself.)
* The code never contains the letters **I, L, O or U**. If you think you see one,
  it is a 1 or a 0. This is deliberate, so do not "correct" it.
* `Verify at idi.africa/verify` stays lowercase — it is for human reading.

## Elsewhere on the certificate

Keep the serial, relabelled:

```
Certificate No. DIDA-IDI-2026-00567
```

This is the organisational record number. It is **not** the verification key and
does not go in the QR.

## Data merge

The admin's **Export merge CSV** action produces one row per certificate with
these columns, ready for InDesign Data Merge or the Figma/Illustrator
variable-data plugins:

```
serial, recipient_full_name, program_title, credential_title,
completion_date, issue_date, venue,
signatory_1_name, signatory_1_title, signatory_2_name, signatory_2_title,
verification_code, verify_url, qr_payload, qr_filename
```

`qr_filename` matches the filenames inside the QR pack ZIP, so the two line up
directly. The CSV deliberately contains **no email addresses**.

## Before printing a run

1. Print one certificate at final size on the real stock.
2. Scan it with at least two different phones.
3. Scan it again in dim light and at roughly 30° off square.
4. Scan it after folding the sheet once across the middle.

If any of those fail, increase the QR to 20 mm before printing the run. Once
certificates are printed the QR cannot be changed.
