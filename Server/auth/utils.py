"""
Cookie utility helpers for authentication.

In development (DEV_MODE=true), cookies are set without the ``secure``
flag and with ``SameSite=Lax`` so that plain-HTTP localhost works.

In production the original settings (secure + SameSite=None) are used
to satisfy modern browser requirements for cross-site cookies.
"""

import os


def cookie_params(max_age: int = 60 * 15) -> dict:
    """Return a dict of cookie flags appropriate for the current environment.

    Parameters
    ----------
    max_age : int
        Cookie lifetime in seconds.  Defaults to 15 minutes (access token).
        Pass ``60 * 60 * 24 * 30`` for a 30-day refresh token.
    """
    dev = os.getenv("DEV_MODE", "false").lower() == "true"
    return {
        "httponly": True,
        "secure": not dev,
        "samesite": "lax" if dev else "none",
        "max_age": max_age,
    }


__all__ = ["cookie_params"]

