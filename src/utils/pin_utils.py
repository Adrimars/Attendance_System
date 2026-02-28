"""
pin_utils.py — Secure PIN hashing with PBKDF2-HMAC-SHA256.

This is the SINGLE source of truth for PIN hashing across the entire
application. No other module should define its own _hash_pin() function.

Backward compatibility:
    verify_pin() detects legacy unsalted SHA-256 hashes (no '$' separator)
    and handles them transparently.  The next PIN change will automatically
    upgrade to the salted format — zero migration friction.
"""

from __future__ import annotations

import hashlib
import hmac
import os

_ITERATIONS = 260_000   # OWASP 2023 recommendation for PBKDF2-SHA256
_SALT_BYTES  = 16


def hash_pin(pin: str) -> str:
    """Hash a PIN with a random salt.

    Returns a string in the format ``'salt_hex$hash_hex'``.
    """
    salt = os.urandom(_SALT_BYTES)
    dk   = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_pin(pin: str, stored: str) -> tuple[bool, bool]:
    """Verify a plaintext PIN against a stored hash.

    Accepts both formats:
    - New format: ``'salt_hex$hash_hex'`` (PBKDF2-HMAC-SHA256 with salt).
    - Legacy format: bare SHA-256 hex string (no ``$`` separator).

    Args:
        pin:    The plaintext PIN entered by the user.
        stored: The value retrieved from the settings table.

    Returns:
        A tuple ``(matches, needs_upgrade)``.
        ``needs_upgrade`` is True when a legacy hash was verified successfully
        and the caller should re-hash with :func:`hash_pin` and persist the
        upgraded value.
    """
    if "$" not in stored:
        # Legacy: plain SHA-256, no salt — constant-time compare
        legacy_hash = hashlib.sha256(pin.encode()).hexdigest()
        matches = hmac.compare_digest(legacy_hash, stored)
        return matches, matches   # needs_upgrade=True only when it matched

    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False, False

    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, _ITERATIONS)
    return hmac.compare_digest(dk.hex(), hash_hex), False
