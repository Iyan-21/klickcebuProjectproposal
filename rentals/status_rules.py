# rentals/status_rules.py
"""
Defines the "normal" forward flow for Booking and Payment statuses.

This is used to tell an expected, automatic step (e.g. Pending -> Confirmed)
apart from an irregular one (skipping ahead, reversing, or moving to a
side-branch status like Cancelled/Refunded/Failed) that requires the admin
to leave a note explaining why.
"""

BOOKING_SEQUENCE = ['pending', 'confirmed', 'ongoing', 'completed']
PAYMENT_SEQUENCE = ['pending', 'paid']


def _is_irregular(sequence, old_status, new_status):
    if old_status == new_status:
        return False
    try:
        old_idx = sequence.index(old_status)
        new_idx = sequence.index(new_status)
    except ValueError:
        # Moving to/from a side-branch status (Cancelled, Refunded, Failed) —
        # always treated as irregular so a reason gets attached.
        return True
    return new_idx != old_idx + 1


def is_irregular_booking_change(old_status, new_status):
    """True if this booking status change skips a step, reverses, or moves
    to/from a side-branch status (e.g. Cancelled) and therefore needs a note."""
    return _is_irregular(BOOKING_SEQUENCE, old_status, new_status)


def is_irregular_payment_change(old_status, new_status):
    """True if this payment status change skips a step, reverses, or moves
    to/from a side-branch status (e.g. Refunded/Failed) and therefore needs a note."""
    return _is_irregular(PAYMENT_SEQUENCE, old_status, new_status)