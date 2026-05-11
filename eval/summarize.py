#!/usr/bin/env python3
"""
summarize.py — Generate CSV summary tables from CiteVQA eval output JSON

Usage:
    python3 summarize.py --input eval_result.json [--out_dir ./]
    python3 summarize.py --input eval_result.json --out_dir /path/to/save/

Output:
    table1_main_metrics.csv   — Rec / Rel / Ans(QA_ACC) / SAA
    table2_bbox_metrics.csv   — Page_Recall / Recall / Precision / F1

Dataset grouping via item["dataset_type"]:
    "Single-Doc"      -> Single-Doc
    "Multi (1-Gold)"   -> Multi (1-Gold)
    "Multi (N-Gold)"   -> Multi (N-Gold)
    Others / Total     -> Overall
"""

import argparse, json, csv, sys
from pathlib import Path
from collections import defaultdict


DATASET_TYPES = ["Single-Doc", "Multi (1-Gold)", "Multi (N-Gold)"]

GROUPS = ["Single-Doc", "Multi (1-Gold)", "Multi (N-Gold)", "Overall"]


def mean_or_none(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


# Scale factors per metric
SCALE = {
    "recall":       100,
    "page_recall":  100,
    "precision":    100,
    "f1":           100,
    "rel":           20,
    "qa_acc":        20,
    "saa":          100,
}


def fmt(v, metric=None):
    if v is None:
        return "-"
    scale = SCALE.get(metric, 1) if metric else 1
    return f"{v * scale:.1f}"


def collect(results):
    """Collect per-group metric scores"""
    buckets = defaultdict(lambda: defaultdict(list))

    for item in results:
        ds = item.get("dataset_type", "")
        group = ds if ds in DATASET_TYPES else "Other"

        for metric in ["recall", "page_recall", "precision", "f1",
                       "rel", "qa_acc", "saa"]:
            key = f"{metric}_score"
            v = item.get(key)
            if v is not None:
                buckets[group][metric].append(v)
                buckets["Overall"][metric].append(v)

    return buckets


def build_table1(buckets):
    """Table1: Rec / Rel / Ans / SAA  x  4 groups"""
    metrics = ["recall", "rel", "qa_acc", "saa"]
    short = ["Rec.", "Rel.", "Ans.", "SAA"]

    header1_merged = [""]
    for g in GROUPS:
        header1_merged.append(g)
        header1_merged += [""] * (len(metrics) - 1)

    header2 = ["Dataset"]
    for g in GROUPS:
        header2 += short

    rows = [header1_merged, header2]

    count_row = ["Count"]
    for g in GROUPS:
        n = len(buckets[g].get("recall", []))
        count_row += [str(n)] + [""] * (len(metrics) - 1)
    rows.append(count_row)

    mean_row = ["Mean"]
    for g in GROUPS:
        for m in metrics:
            mean_row.append(fmt(mean_or_none(buckets[g].get(m, [])), m))
    rows.append(mean_row)

    return rows


def build_table2(buckets):
    """Table2: Page_Recall / Rec / Precision / F1  x  4 groups"""
    metrics = ["page_recall", "recall", "precision", "f1"]
    short = ["Page_Recall", "Rec.", "Precision", "F1"]

    header1_merged = [""]
    for g in GROUPS:
        header1_merged.append(g)
        header1_merged += [""] * (len(metrics) - 1)

    header2 = ["Dataset"]
    for g in GROUPS:
        header2 += short

    rows = [header1_merged, header2]

    count_row = ["Count"]
    for g in GROUPS:
        n = len(buckets[g].get("recall", []))
        count_row += [str(n)] + [""] * (len(metrics) - 1)
    rows.append(count_row)

    mean_row = ["Mean"]
    for g in GROUPS:
        for m in metrics:
            mean_row.append(fmt(mean_or_none(buckets[g].get(m, [])), m))
    rows.append(mean_row)

    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    print(f"  Written: {path}")


def main():
    p = argparse.ArgumentParser(description="CiteVQA eval results to CSV summary")
    p.add_argument("--input", required=True, help="Eval output JSON file")
    p.add_argument("--out_dir", default="", help="CSV output directory (default: same dir as input)")
    a = p.parse_args()

    inp = Path(a.input)
    if not inp.exists():
        print(f"File not found: {inp}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(a.out_dir) if a.out_dir else inp.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(inp, encoding="utf-8") as f:
        data = json.load(f)

    results = data if isinstance(data, list) else data.get("results", [])
    print(f"Loaded {len(results)} eval results")

    # Dataset distribution
    from collections import Counter
    ds_counter = Counter(item.get("dataset_type", "<none>") for item in results)
    print("Dataset distribution:", dict(ds_counter))

    buckets = collect(results)

    stem = inp.stem
    t1_path = out_dir / f"{stem}_table1_main_metrics.csv"
    t2_path = out_dir / f"{stem}_table2_bbox_metrics.csv"

    write_csv(build_table1(buckets), t1_path)
    write_csv(build_table2(buckets), t2_path)
    print("Done.")


if __name__ == "__main__":
    main()
