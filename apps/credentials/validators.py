"""File validators. The first in this project -- nothing else validates uploads."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB, comfortably inside the 25 MB upload cap
PDF_MAGIC = b'%PDF-'


def validate_pdf_size(value):
    if value.size > MAX_PDF_BYTES:
        raise ValidationError(
            f'That file is {value.size / 1_048_576:.1f} MB. '
            f'The limit is {MAX_PDF_BYTES // 1_048_576} MB.'
        )


@deconstructible
class PdfMagicBytesValidator:
    """Check the file really is a PDF, not just named like one.

    An extension check alone is trivially bypassed. Note the ``seek(0)`` at the
    end: forgetting it is the classic bug here -- the read cursor stays advanced
    and the stored file silently loses its first five bytes.
    """

    def __call__(self, value):
        file = value.file if hasattr(value, 'file') else value
        try:
            position = file.tell()
        except (AttributeError, OSError):
            position = 0
        try:
            file.seek(0)
            header = file.read(len(PDF_MAGIC))
        finally:
            file.seek(position or 0)

        if header != PDF_MAGIC:
            raise ValidationError('That file is not a PDF.')

    def __eq__(self, other):
        return isinstance(other, PdfMagicBytesValidator)
