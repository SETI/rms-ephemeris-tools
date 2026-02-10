"""Run specification: tool type and parameters (CLI/env compatible)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote


def _query_pairs(p: dict[str, Any], tool: str) -> list[tuple[str, str]]:
    """Build (name, value) pairs for QUERY_STRING (CGI GET). FORTRAN reads
    form params from QUERY_STRING via getcgivars(), not from env vars.
    """
    pairs: list[tuple[str, str]] = []
    if "start" in p and p["start"]:
        pairs.append(("start", str(p["start"])))
    if "stop" in p and p["stop"]:
        pairs.append(("stop", str(p["stop"])))
    if "interval" in p:
        pairs.append(("interval", str(p["interval"])))
    if "time_unit" in p:
        pairs.append(("time_unit", str(p["time_unit"])))
    if "ephem" in p:
        pairs.append(("ephem", str(p["ephem"])))
    if "viewpoint" in p:
        pairs.append(("viewpoint", str(p["viewpoint"])))
    if "observatory" in p:
        pairs.append(("observatory", str(p["observatory"])))
    if "latitude" in p and p["latitude"] is not None:
        pairs.append(("latitude", str(p["latitude"])))
    if "longitude" in p and p["longitude"] is not None:
        pairs.append(("longitude", str(p["longitude"])))
    if "lon_dir" in p:
        pairs.append(("lon_dir", str(p["lon_dir"])))
    if "altitude" in p and p["altitude"] is not None:
        pairs.append(("altitude", str(p["altitude"])))
    if "sc_trajectory" in p:
        pairs.append(("sc_trajectory", str(p["sc_trajectory"])))
    for col in p.get("columns") or []:
        pairs.append(("columns", str(col)))
    for col in p.get("mooncols") or []:
        pairs.append(("mooncols", str(col)))
    for moon in p.get("moons") or []:
        pairs.append(("moons", str(moon)))
    if tool == "viewer":
        if "time" in p and p["time"]:
            pairs.append(("time", str(p["time"])))
        if "fov" in p:
            pairs.append(("fov", str(p["fov"])))
        if "fov_unit" in p:
            pairs.append(("fov_unit", str(p["fov_unit"])))
        if "center" in p:
            pairs.append(("center", str(p["center"])))
        if "center_body" in p:
            pairs.append(("center_body", str(p["center_body"])))
        if "center_ra" in p:
            pairs.append(("center_ra", str(p["center_ra"])))
        if "center_dec" in p:
            pairs.append(("center_dec", str(p["center_dec"])))
        if "rings" in p and p["rings"] is not None:
            r = p["rings"]
            rings_str = " ".join(str(x) for x in (r if isinstance(r, list) else [r]))
            pairs.append(("rings", rings_str))
        if "title" in p:
            pairs.append(("title", str(p["title"])))
    return pairs


@dataclass
class RunSpec:
    """Single run specification for ephemeris, tracker, or viewer.

    Parameters match CGI/env names and Python CLI. Used to drive both
    FORTRAN (via environment) and Python (via CLI or env).
    """

    tool: str  # "ephemeris" | "tracker" | "viewer"
    params: dict[str, Any] = field(default_factory=dict)

    def env_for_fortran(self, table_path: str | None = None, ps_path: str | None = None) -> dict[str, str]:
        """Build environment dict for FORTRAN (CGI-style).

        FORTRAN reads form parameters from QUERY_STRING (parsed when
        REQUEST_METHOD=GET). Only NPLANET, EPHEM_FILE, TRACKER_POSTFILE,
        TRACKER_TEXTFILE, VIEWER_POSTFILE, VIEWER_TEXTFILE are read
        via WWW_GetEnv and must be set as env vars.
        """
        env: dict[str, str] = {}
        p = self.params

        # Required by getcgivars(): REQUEST_METHOD=GET and QUERY_STRING.
        # Without these the C code exits (e.g. "Unsupported REQUEST_METHOD").
        env["REQUEST_METHOD"] = "GET"
        pairs = _query_pairs(p, self.tool)
        env["QUERY_STRING"] = "&".join(
            f"{quote(name)}={quote(value)}" for name, value in pairs
        )

        # These are read via WWW_GetEnv(), not from QUERY_STRING.
        if "planet" in p:
            env["NPLANET"] = str(int(p["planet"]))
        if self.tool == "ephemeris" and table_path:
            env["EPHEM_FILE"] = table_path
        if self.tool == "tracker":
            if ps_path:
                env["TRACKER_POSTFILE"] = ps_path
            if table_path:
                env["TRACKER_TEXTFILE"] = table_path
        if self.tool == "viewer":
            if ps_path:
                env["VIEWER_POSTFILE"] = ps_path
            if table_path:
                env["VIEWER_TEXTFILE"] = table_path

        return env

    def cli_args_for_python(self) -> list[str]:
        """Build CLI argument list for ephemeris-tools."""
        args = [self.tool]
        p = self.params
        if "planet" in p:
            args.extend(["--planet", str(int(p["planet"]))])
        if self.tool in ("ephemeris", "tracker") and "start" in p and p["start"]:
            args.extend(["--start", str(p["start"])])
        if self.tool in ("ephemeris", "tracker") and "stop" in p and p["stop"]:
            args.extend(["--stop", str(p["stop"])])
        if "interval" in p:
            args.extend(["--interval", str(p["interval"])])
        if "time_unit" in p:
            args.extend(["--time-unit", str(p["time_unit"])])
        if "ephem" in p:
            args.extend(["--ephem", str(p["ephem"])])
        if "viewpoint" in p:
            args.extend(["--viewpoint", str(p["viewpoint"])])
        if "observatory" in p:
            args.extend(["--observatory", str(p["observatory"])])
        if "latitude" in p and p["latitude"] is not None:
            args.extend(["--latitude", str(p["latitude"])])
        if "longitude" in p and p["longitude"] is not None:
            args.extend(["--longitude", str(p["longitude"])])
        if "lon_dir" in p:
            args.extend(["--lon-dir", str(p["lon_dir"])])
        if "altitude" in p and p["altitude"] is not None:
            args.extend(["--altitude", str(p["altitude"])])
        if "sc_trajectory" in p:
            args.extend(["--sc-trajectory", str(p["sc_trajectory"])])
        if "columns" in p and p["columns"]:
            args.append("--columns")
            args.extend(str(c) for c in p["columns"])
        if "mooncols" in p and p["mooncols"]:
            args.append("--mooncols")
            args.extend(str(c) for c in p["mooncols"])
        if "moons" in p and p["moons"]:
            args.append("--moons")
            args.extend(str(m) for m in p["moons"])
        if self.tool == "viewer":
            if "time" in p and p["time"]:
                args.extend(["--time", str(p["time"])])
            if "fov" in p:
                args.extend(["--fov", str(p["fov"])])
            if "fov_unit" in p:
                args.extend(["--fov-unit", str(p["fov_unit"])])
            if "center" in p:
                args.extend(["--center", str(p["center"])])
            if "center_body" in p:
                args.extend(["--center-body", str(p["center_body"])])
            if "rings" in p and p["rings"]:
                args.append("--rings")
                args.extend(str(r) for r in (p["rings"] if isinstance(p["rings"], list) else [p["rings"]]))
            if "title" in p:
                args.extend(["--title", str(p["title"])])
        if self.tool == "tracker" and "rings" in p and p["rings"]:
            args.append("--rings")
            args.extend(str(r) for r in (p["rings"] if isinstance(p["rings"], list) else [p["rings"]]))
        if self.tool == "tracker":
            if "xrange" in p and p["xrange"] is not None:
                args.extend(["--xrange", str(p["xrange"])])
            if "xunit" in p:
                args.extend(["--xunit", str(p["xunit"])])
        return args
