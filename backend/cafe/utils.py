"""Utility helpers for # 91 VRS Cafe backend."""

from __future__ import annotations

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
