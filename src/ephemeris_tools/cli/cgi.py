"""CGI-compatible parameter reading from environment (replaces MyWWW/Perl)."""

from __future__ import annotations

import os
import re


def get_key(name: str, default: str | None = '') -> str:
    """Read one parameter from environment (WWW_GetKey). Sanitized."""
    raw = os.environ.get(name, default)
    return _sanitize(str(raw).strip())


def get_keys(name: str) -> list[str]:
    """Read repeated parameters (WWW_GetKeys). Returns list of values.

    Env vars like COLUMNS#1, COLUMNS#2 or COLUMNS=1#2#3 (split on #).
    """
    out: list[str] = []
    seen = set()
    i = 1
    while True:
        v = os.environ.get(f'{name}#{i}', '').strip()
        if not v and i == 1:
            v = os.environ.get(name, '').strip()
        if not v:
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
    if not out:
        single = os.environ.get(name, '').strip()
        if single:
            for part in re.split(r'[\s,#]+', single):
                if part:
                    sanitized = _sanitize(part)
                    if sanitized not in seen:
                        seen.add(sanitized)
                        out.append(sanitized)
    return out


def get_env(name: str, default: str | None = '') -> str:
    """Read environment variable (WWW_GetEnv). No sanitization."""
    raw = os.environ.get(name, default)
    return str(raw).strip()


def _sanitize(s: str) -> str:
    """Basic sanitization: remove control chars and limit length."""
    s = ''.join(c for c in s if ord(c) >= 32 and ord(c) != 127)
    return s[:256] if len(s) > 256 else s
