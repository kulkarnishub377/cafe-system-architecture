"""Custom API exceptions for SK Cafe."""

from rest_framework import status
from rest_framework.exceptions import APIException


class CafeAPIException(APIException):
    """Base exception for all cafe-specific API errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A cafe API error occurred.'
    default_code = 'cafe_error'


class TableOccupied(CafeAPIException):
    """Raised when trying to open a session on a table that already has one."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This table already has an active session.'
    default_code = 'table_occupied'


class InvalidDiscount(CafeAPIException):
    """Raised when a discount code is invalid, expired, or exhausted."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Discount code is invalid or has expired.'
    default_code = 'invalid_discount'


class ReservationConflict(CafeAPIException):
    """Raised when a conflicting reservation already exists for a table/time slot."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A reservation already exists for this table at the requested time.'
    default_code = 'reservation_conflict'


class MenuItemOutOfStock(CafeAPIException):
    """Raised when one or more requested menu items are currently out of stock."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'One or more items are out of stock.'
    default_code = 'out_of_stock'
