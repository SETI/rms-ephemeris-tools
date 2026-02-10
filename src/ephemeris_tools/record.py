"""Tabular output record formatting (ported from ephem3_xxx.f Rec_Init/Rec_Append/Rec_Write)."""

from __future__ import annotations

from typing import TextIO


class Record:
    """Fixed-width record buffer: append fields with a single blank separator, then write line."""

    def __init__(self, max_length: int = 4096) -> None:
        """Allocate a record buffer of max_length characters."""
        self._parts: list[str] = []
        self._max_length = max_length
        self._length = -1

    def init(self) -> None:
        """Clear the record and reset length (FORTRAN Rec_Init)."""
        self._parts = []
        self._length = -1

    def append(self, string: str) -> None:
        """Append a field: one blank before field except the first (FORTRAN Rec_Append)."""
        self._length += 1
        remaining = self._max_length - self._length
        if remaining <= 0:
            return
        to_add = string[:remaining] if len(string) > remaining else string
        if self._parts:
            self._parts.append(" ")
            self._length += 1
        self._parts.append(to_add)
        self._length += len(to_add)

    def write(self, stream: TextIO) -> None:
        """Write the current record line and re-initialize (FORTRAN Rec_Write)."""
        if self._length >= 0:
            line = "".join(self._parts).rstrip()
            if line:
                stream.write(line + "\n")
        self.init()

    def get_line(self) -> str:
        """Return current record as a string without writing or re-initializing."""
        if self._length < 0:
            return ""
        return "".join(self._parts).rstrip()
