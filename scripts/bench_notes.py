#!/usr/bin/env python3
"""Full-year 2026 press at several --notes-pages N; record time/RSS/PDF stats.

Stops at the first OOM / SIGKILL / allocator death. Writes
artifacts/bench-notes.json for BENCH.md.

Named dests: ReportLab Catalog /Dests. pypdf lists them with a leading slash
(e.g. /day-2026-07-02). Counts and spot-checks use that map.
"""

from __future__ import annotations

import json
import re
import signal
import subprocess
import sys
from datetime import date
from pathlib import Path

YEAR = 2026
MID_DAY = date(2026, 7, 2)
ORDER = (0, 2, 10, 20, 30, 50, 100)
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path("/tmp/planner-bench")
JSON_PATH = ROOT / "artifacts" / "bench-notes.json"
TIME_BIN = "/usr/bin/time"
PRESS = str(ROOT / ".venv" / "bin" / "press")
if not Path(PRESS).is_file():
    PRESS = "press"

FATAL_SIGNALS = {signal.SIGKILL, signal.SIGSEGV, signal.SIGABRT, signal.SIGBUS}


def dest_day(day: date) -> str:
    return f"day-{day.isoformat()}"


def dest_notes(day: date, n: int) -> str:
    return f"day-{day.isoformat()}-notes-{n}"


def _lookup_dest(reader, name: str):
    dests = reader.named_destinations
    return dests.get(name) or dests.get("/" + name.lstrip("/"))


def parse_time_verbose(text: str) -> dict:
    def grab(label: str) -> str | None:
        m = re.search(rf"{re.escape(label)}:\s*(.+)", text)
        return m.group(1).strip() if m else None

    elapsed_raw = grab("Elapsed (wall clock) time (h:mm:ss or m:ss)")
    rss_raw = grab("Maximum resident set size (kbytes)")
    status_raw = grab("Exit status")
    elapsed_s = _parse_elapsed(elapsed_raw) if elapsed_raw else None
    rss_kb = int(rss_raw) if rss_raw and rss_raw.isdigit() else None
    exit_status = int(status_raw) if status_raw and status_raw.lstrip("-").isdigit() else None
    return {
        "elapsed_raw": elapsed_raw,
        "elapsed_s": elapsed_s,
        "peak_rss_kb": rss_kb,
        "peak_rss_mib": round(rss_kb / 1024, 1) if rss_kb is not None else None,
        "time_exit_status": exit_status,
        "time_verbose": text.strip(),
    }


def _parse_elapsed(raw: str) -> float:
    parts = raw.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(raw)


def inspect_pdf(path: Path, notes_n: int) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    dests = reader.named_destinations
    links = 0
    for page in reader.pages:
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            if obj.get("/Subtype") == "/Link":
                links += 1

    day_name = dest_day(MID_DAY)
    notes1_name = dest_notes(MID_DAY, 1)
    day_page = _dest_page(reader, day_name)
    notes1_page = _dest_page(reader, notes1_name) if notes_n >= 1 else None
    day_to_notes = (
        _page_links_to(reader, day_page, notes1_page) if day_page and notes1_page else False
    )
    notes_to_day = (
        _page_links_to(reader, notes1_page, day_page) if day_page and notes1_page else False
    )
    return {
        "pages": len(reader.pages),
        "named_dests": len(dests),
        "named_dests_how": "pypdf named_destinations from ReportLab Catalog /Dests (keys like /day-YYYY-MM-DD)",
        "link_annots": links,
        "bytes": path.stat().st_size,
        "spot": {
            "day": day_name,
            "day_dest": day_page is not None,
            "day_page": day_page,
            "notes1": notes1_name,
            "notes1_dest": notes1_page is not None,
            "notes1_page": notes1_page,
            "day_to_notes1": day_to_notes,
            "notes1_to_day": notes_to_day,
        },
    }


def _dest_page(reader, name: str) -> int | None:
    dest = _lookup_dest(reader, name)
    if dest is None:
        return None
    return reader.get_destination_page_number(dest) + 1


def _page_links_to(reader, from_page: int, to_page: int) -> bool:
    src = reader.pages[from_page - 1]
    target = reader.pages[to_page - 1].indirect_reference
    want = _lookup_dest(reader, dest_day(MID_DAY))
    for annot in src.get("/Annots") or []:
        obj = annot.get_object()
        dest = obj.get("/Dest")
        if dest is None:
            action = obj.get("/A")
            dest = action.get("/D") if action else None
        if dest is None:
            continue
        if hasattr(dest, "get") and dest.get("/Page") == target:
            return True
        try:
            if dest[0] == target:
                return True
        except (TypeError, KeyError):
            pass
        # named dest string
        if dest in (f"/day-{MID_DAY.isoformat()}", dest_day(MID_DAY)):
            if from_page != to_page:
                # only treat as day-target when checking notes→day
                pass
    # resolve via dest page number of named dest in annot
    for annot in src.get("/Annots") or []:
        obj = annot.get_object()
        dest = obj.get("/Dest")
        if dest is None:
            continue
        try:
            if dest[0] == target:
                return True
        except (TypeError, KeyError, IndexError):
            continue
    return False


def is_fatal_resource(returncode: int | None) -> tuple[bool, str]:
    if returncode is None:
        return True, "no return code"
    if returncode == 0:
        return False, ""
    if returncode < 0:
        sig = -returncode
        if sig in FATAL_SIGNALS:
            return True, f"signal {sig} ({signal.Signals(sig).name})"
        return True, f"signal {sig}"
    if returncode >= 128:
        sig = returncode - 128
        try:
            name = signal.Signals(sig).name
        except ValueError:
            name = str(sig)
        if sig in {s.value for s in FATAL_SIGNALS} or sig == signal.SIGKILL:
            return True, f"exit {returncode} (128+{sig} {name})"
        return True, f"exit {returncode} (128+{sig} {name})"
    return False, f"exit {returncode}"


def run_one(n: int) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / f"planner-{YEAR}-notes{n}.pdf"
    time_path = OUT_DIR / f"time-notes{n}.txt"
    if pdf_path.exists():
        pdf_path.unlink()
    press_cmd = [PRESS, "--year", str(YEAR), "--notes-pages", str(n), "-o", str(pdf_path)]
    cmd = [TIME_BIN, "-v", "-o", str(time_path), *press_cmd] if Path(TIME_BIN).is_file() else press_cmd
    print(f"\n=== N={n} ===", flush=True)
    print(" ".join(cmd), flush=True)
    import resource
    import time as time_mod

    t0 = time_mod.perf_counter()
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    wall_s = time_mod.perf_counter() - t0
    child_rss_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    time_text = time_path.read_text() if time_path.is_file() else ""
    time_info = parse_time_verbose(time_text) if time_text else {}
    if time_info.get("elapsed_s") is None:
        time_info["elapsed_s"] = round(wall_s, 3)
        time_info["elapsed_raw"] = f"{wall_s:.3f}s (perf_counter)"
    if time_info.get("peak_rss_kb") is None and child_rss_kb:
        time_info["peak_rss_kb"] = int(child_rss_kb)
        time_info["peak_rss_mib"] = round(child_rss_kb / 1024, 1)
    row: dict = {
        "n": n,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
        **time_info,
        "pdf_path": str(pdf_path),
        "completed": False,
        "fatal": False,
        "fatal_reason": "",
    }
    fatal, reason = is_fatal_resource(proc.returncode)
    if proc.returncode != 0:
        if "MemoryError" in (proc.stderr or "") or "Cannot allocate" in (proc.stderr or ""):
            fatal = True
            reason = reason or "allocator / MemoryError"
        row["fatal"] = True
        row["fatal_reason"] = reason or f"exit {proc.returncode}"
        print(f"FAILED N={n}: {row['fatal_reason']}", flush=True)
        if proc.stderr:
            print(proc.stderr[-2000:], flush=True)
        return row

    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        row["fatal"] = True
        row["fatal_reason"] = "press exited 0 but PDF missing/empty"
        return row

    print(f"inspect {pdf_path} ({pdf_path.stat().st_size} bytes)", flush=True)
    stats = inspect_pdf(pdf_path, n)
    row.update(stats)
    row["completed"] = True
    print(
        f"N={n} pages={stats['pages']} dests={stats['named_dests']} "
        f"annots={stats['link_annots']} bytes={stats['bytes']} "
        f"wall={row.get('elapsed_s')}s rss={row.get('peak_rss_mib')}MiB "
        f"spot={stats['spot']}",
        flush=True,
    )
    if n > 0 and pdf_path.stat().st_size > 2_000_000:
        pdf_path.unlink()
        row["pdf_deleted_after_measure"] = True
    return row


def main(argv: list[str] | None = None) -> int:
    ns = [int(x) for x in (argv or sys.argv[1:] or ORDER)]
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    stopped_at: int | None = None
    last_ok: int | None = None
    for n in ns:
        row = run_one(n)
        rows.append(row)
        JSON_PATH.write_text(json.dumps({"order": ns, "rows": rows}, indent=2))
        if row.get("completed"):
            last_ok = n
            continue
        stopped_at = n
        print(f"Stopping: N={n} failed ({row.get('fatal_reason')}). Last completed N={last_ok}.")
        break
    summary = {"order": ns, "last_completed_n": last_ok, "died_n": stopped_at, "rows": rows}
    JSON_PATH.write_text(json.dumps(summary, indent=2))
    print(f"wrote {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
