"""Utility helpers for # SK cafe backend."""

from __future__ import annotations

import base64
import io
from typing import Any


def calculate_bill(
    items: list[dict[str, Any]],
    tax_rate: float,
    discount_amount: int = 0,
) -> dict[str, int]:
    """
    Compute the full bill breakdown for a list of ordered items.

    Args:
        items: List of dicts, each with ``'price'`` (int) and ``'qty'`` (int).
        tax_rate: Tax percentage to apply (e.g. ``5.0`` for 5 %).
        discount_amount: Flat discount in INR to deduct before tax.

    Returns:
        Dict with keys ``subtotal``, ``discount``, ``tax``, and ``total``
        (all values are integer INR amounts).
    """
    subtotal: int = sum(i['price'] * i['qty'] for i in items)
    taxable: int = max(0, subtotal - discount_amount)
    tax: int = round(taxable * tax_rate / 100)
    total: int = taxable + tax
    return {
        'subtotal': subtotal,
        'discount': discount_amount,
        'tax': tax,
        'total': total,
    }


def generate_qr_url(table_number: int, base_url: str = 'http://127.0.0.1:8000') -> str:
    """
    Generate the customer-facing ordering URL used in a table's QR code.

    Args:
        table_number: The physical table number.
        base_url: Base URL of the deployment (no trailing slash).

    Returns:
        Full URL string pointing to the table's QR redirect endpoint.
    """
    return f'{base_url}/api/tables/{table_number}/qr_redirect/'


def generate_qr_code_base64(
    url: str,
    box_size: int = 10,
    border: int = 4,
) -> str:
    """
    Generate a QR code PNG image for *url* and return it as a base64-encoded string.

    The result is a plain base64 string (no ``data:image/png;base64,`` prefix).
    Use ``generate_qr_code_data_uri()`` to get a data URI ready for ``<img src>``.

    Args:
        url: The URL to encode in the QR code.
        box_size: Size in pixels of each QR box (module).
        border: Number of box-widths to use as the quiet-zone border.

    Returns:
        Base64-encoded PNG string.
    """
    import qrcode  # local import so the module is optional at test time

    qr = qrcode.QRCode(
        version=None,  # auto-select
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def generate_qr_code_data_uri(url: str, **kwargs) -> str:
    """
    Convenience wrapper that returns a complete ``data:`` URI.

    Returns:
        A string like ``data:image/png;base64,<b64data>`` safe for use in
        ``<img src="...">``.
    """
    b64 = generate_qr_code_base64(url, **kwargs)
    return f'data:image/png;base64,{b64}'


def get_greeting(hour: int) -> str:
    """
    Return a time-appropriate greeting string.

    Args:
        hour: Current hour in 24-hour format (0–23).

    Returns:
        Greeting string: 'Good Morning', 'Good Afternoon', 'Good Evening',
        or 'Good Night'.
    """
    if 5 <= hour < 12:
        return 'Good Morning'
    if 12 <= hour < 17:
        return 'Good Afternoon'
    if 17 <= hour < 21:
        return 'Good Evening'
    return 'Good Night'


def get_client_ip(request) -> str:
    """Extract the real client IP address from a Django request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''
