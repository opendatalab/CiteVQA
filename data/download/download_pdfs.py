#!/usr/bin/env python3
"""
Concurrent PDF download tool

Usage:
  python download_pdfs.py [options]

Options:
  --csv       CSV file path (default: pdf_source.csv in the same directory)
  --out       Output directory (default: ../pdf)
  --workers   Number of concurrent threads (default: 16)
  --timeout   Per-file timeout in seconds (default: 120)
  --retries   Retry count on failure (default: 3)
  --skip      Skip existing files (default: True)
"""
import argparse
import csv
import os
import sys
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from tqdm import tqdm

# ── Default paths ─────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "pdf_source.csv"
DEFAULT_OUT = SCRIPT_DIR.parent / "pdf"


def parse_args():
    p = argparse.ArgumentParser(description="Concurrent PDF downloader")
    p.add_argument("--csv",      default=str(DEFAULT_CSV), help="CSV file path")
    p.add_argument("--out",      default=str(DEFAULT_OUT), help="PDF output directory")
    p.add_argument("--workers",  type=int, default=16,     help="Number of concurrent workers")
    p.add_argument("--timeout",  type=int, default=120,    help="Per-file timeout (seconds)")
    p.add_argument("--retries",  type=int, default=3,      help="Retry count on failure")
    p.add_argument("--no-skip",  action="store_true",      help="Do not skip existing files")
    return p.parse_args()


def url_to_filename(track_id: str, url: str) -> str:
    """Use track_id as filename with .pdf extension"""
    parsed = urlparse(url)
    path = parsed.path.split("?")[0]
    suffix = Path(path).suffix.lower() or ".pdf"
    if suffix != ".pdf":
        suffix = ".pdf"
    return f"{track_id}{suffix}"


def download_one(track_id: str, url: str, out_path: Path,
                 timeout: int, retries: int, skip: bool):
    if skip and out_path.exists() and out_path.stat().st_size > 0:
        return "skip", track_id, None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, stream=True,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return "ok", track_id, None
        except Exception as e:
            if attempt == retries:
                return "fail", track_id, str(e)
            time.sleep(2 ** attempt)   # exponential backoff


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    out_dir  = Path(args.out)
    skip     = not args.no_skip

    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Read task list
    tasks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id = row.get("track_id", "").strip()
            url      = row.get("url", "").strip()
            if not track_id or not url:
                continue
            filename = url_to_filename(track_id, url)
            out_path = out_dir / filename
            tasks.append((track_id, url, out_path))

    print(f"Total {len(tasks)} PDFs, output directory: {out_dir}")
    print(f"Workers: {args.workers}  Timeout: {args.timeout}s  Retries: {args.retries}  Skip existing: {skip}")

    ok_count   = 0
    skip_count = 0
    fail_list  = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(download_one, tid, url, op, args.timeout, args.retries, skip): tid
            for tid, url, op in tasks
        }
        pbar = tqdm(as_completed(futures), total=len(futures), unit="file")
        for fut in pbar:
            status, tid, err = fut.result()
            if status == "ok":
                ok_count += 1
            elif status == "skip":
                skip_count += 1
            else:
                fail_list.append((tid, err))
            pbar.set_postfix(ok=ok_count, skip=skip_count, fail=len(fail_list))

    # ── Summary ─────────────────────────────────────────────
    print(f"\n✅ Downloaded: {ok_count}")
    print(f"⏭  Skipped:    {skip_count}")
    print(f"❌ Failed:     {len(fail_list)}")

    if fail_list:
        fail_log = out_dir / "failed.txt"
        with open(fail_log, "w") as f:
            for tid, err in fail_list:
                f.write(f"{tid}\t{err}\n")
        print(f"Failed list saved to: {fail_log}")


if __name__ == "__main__":
    main()
