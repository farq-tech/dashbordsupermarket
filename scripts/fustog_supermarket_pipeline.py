#!/usr/bin/env python3
"""
Supermarket dashboard data from Fustog (فستق):

1) fetch_fustog_live_bundle.py — يجلب bundle + CSVs من API إلى data/
2) build_live_exports.py — يبني fustog_stores_lookup / enriched_long / matching_summary
   وينسخها إلى platform/data_supermarket/ للتبويب «سوبرماركت» في الداشبورد.

تشغيل من جذر المشروع:
  python scripts/fustog_supermarket_pipeline.py
  python scripts/fustog_supermarket_pipeline.py --skip-fetch   # إذا عندك bundle جاهز في data/
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description="Fustog → supermarket dashboard CSVs")
    ap.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Do not run fetch_fustog_live_bundle.py (use latest files in data/)",
    )
    ap.add_argument(
        "--no-dashboard-copy",
        action="store_true",
        help="Pass through to build_live_exports (no copy to platform/data_supermarket)",
    )
    args = ap.parse_args()

    if not args.skip_fetch:
        fetch = REPO_ROOT / "scripts" / "fetch_fustog_live_bundle.py"
        r = subprocess.run([sys.executable, str(fetch)], cwd=str(REPO_ROOT))
        if r.returncode != 0:
            return r.returncode

    build = REPO_ROOT / "scripts" / "build_live_exports.py"
    cmd = [sys.executable, str(build)]
    if args.no_dashboard_copy:
        cmd.append("--no-dashboard-copy")
    r = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
