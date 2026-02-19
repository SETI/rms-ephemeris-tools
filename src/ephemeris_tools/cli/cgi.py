"""CGI-compatible parameter reading from environment (replaces MyWWW/Perl)."""

from __future__ import annotations

import os
import re


def get_key(name: str, default: str | None = '') -> str:
    """Read one CGI parameter from environment (WWW_GetKey).

    Parameters:
        name: Environment variable name.
        default: Value if name is missing.

    Returns:
        Sanitized, stripped string.
    """
    raw = os.environ.get(name, default)
    return _sanitize(str(raw).strip())


def get_keys(name: str) -> list[str]:
    """Read repeated CGI parameters (WWW_GetKeys): name, name#1, name#2 or split.

    Parameters:
        name: Base environment variable name.

    Returns:
        List of sanitized values (no duplicates, order preserved).
    """
    out: list[str] = []
    seen = set()
    i = 1
    while True:
        v = os.environ.get(f'{name}#{i}', '').strip()
        if len(v) == 0 and i == 1:
            v = os.environ.get(name, '').strip()
        if len(v) == 0:
            break
        if '#' in v:
            parts = [p.strip() for p in v.split('#') if p.strip()]
            for p in parts:
                if p not in seen:
                    seen.add(p)
                    out.append(_sanitize(p))
            i += 1
            continue
        if v not in seen:
            seen.add(v)
            out.append(_sanitize(v))
        i += 1
    if len(out) == 0:
        single = os.environ.get(name, '').strip()
        if len(single) > 0:
            for part in re.split(r'[\s,#]+', single):
                if len(part) > 0:
                    sanitized = _sanitize(part)
                    if sanitized not in seen:
                        seen.add(sanitized)
                        out.append(sanitized)
    return out


def get_env(name: str, default: str | None = '') -> str:
    """Read environment variable (WWW_GetEnv); no sanitization.

    Parameters:
        name: Environment variable name.
        default: Value if name is missing.

    Returns:
        Stripped string.
    """
    raw = os.environ.get(name, default)
    return str(raw).strip()


def _sanitize(s: str) -> str:
    """Basic sanitization: remove control chars and limit length to 256.

    Returns:
        Sanitized string.
    """
    s = ''.join(c for c in s if ord(c) >= 32 and ord(c) != 127)
    return s[:256] if len(s) > 256 else s
