#!/usr/bin/env python3
"""Merge freshly fetched sugar prices into data/data.json and data/sugar_daily.csv.

Usage:
  python scripts/merge_update.py active          # print symbols that still trade (JSON list)
  python scripts/merge_update.py merge FILE      # merge lines "SYM,YYYY-MM-DD,close" from FILE

The merge only adds or corrects dates; it never deletes history. It refuses
obviously bad input (unknown symbol, non-positive price, >25% jump vs the
previous close) and exits non-zero without writing anything in that case.
"""
import csv, datetime as dt, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "data", "data.json")
CSV_PATH = os.path.join(ROOT, "data", "sugar_daily.csv")
FAMILIES = ["SWH", "SWK", "SWQ", "SBH", "SBK", "SBN"]
SYM_RE = re.compile(r"^(SW[HKQ]|SB[HKN])\d\d$")


def scale(sym):
    return 100 if sym.startswith("SB") else 10


def decode(sym, packed):
    start, gaps, closes = packed
    d = dt.date.fromisoformat(start)
    out = []
    for g, c in zip(gaps, closes):
        d += dt.timedelta(days=g)
        out.append((d.isoformat(), round(c / scale(sym), 4)))
    return out


def encode(sym, rows):
    prev = dt.date.fromisoformat(rows[0][0])
    gaps, closes = [], []
    for d, c in rows:
        dd = dt.date.fromisoformat(d)
        gaps.append((dd - prev).days)
        prev = dd
        closes.append(round(c * scale(sym)))
    return [rows[0][0], gaps, closes]


def load():
    with open(JSON_PATH) as f:
        return json.load(f)


def active(data):
    lasts = {s: decode(s, p)[-1][0] for s, p in data["symbols"].items()}
    newest = max(lasts.values())
    cutoff = (dt.date.fromisoformat(newest) - dt.timedelta(days=10)).isoformat()
    return sorted(s for s, last in lasts.items() if last >= cutoff)


def merge(data, path):
    new = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            sym, day, close = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if not SYM_RE.match(sym):
                sys.exit(f"bad symbol: {line}")
            dt.date.fromisoformat(day)
            value = float(close)
            if value <= 0:
                sys.exit(f"non-positive price: {line}")
            new.setdefault(sym, {})[day] = value
    if not new:
        sys.exit("no price lines found in input")
    report = []
    for sym, days in sorted(new.items()):
        rows = dict(decode(sym, data["symbols"][sym])) if sym in data["symbols"] else {}
        added = [d for d in days if d not in rows]
        changed = [d for d in days if d in rows and abs(rows[d] - days[d]) > 1e-9]
        rows.update(days)
        ordered = sorted(rows.items())
        for (d0, c0), (d1, c1) in zip(ordered, ordered[1:]):
            if d1 in days and abs(c1 / c0 - 1) > 0.25:
                sys.exit(f"{sym}: suspicious jump {d0} {c0} -> {d1} {c1}")
        data["symbols"][sym] = encode(sym, ordered)
        report.append(f"{sym}: +{len(added)} new day(s), {len(changed)} corrected, last {ordered[-1][0]} = {ordered[-1][1]}")
    return report


def write(data, changed):
    data["last_date"] = max(decode(s, p)[-1][0] for s, p in data["symbols"].items())
    if changed:
        data["generated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["contract", "date", "close"])
        for sym in sorted(data["symbols"]):
            for d, c in decode(sym, data["symbols"][sym]):
                w.writerow([sym, d, c])


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("active", "merge"):
        sys.exit(__doc__)
    data = load()
    if sys.argv[1] == "active":
        print(json.dumps(active(data)))
        return
    before = json.dumps(data["symbols"], sort_keys=True)
    report = merge(data, sys.argv[2])
    changed = json.dumps(data["symbols"], sort_keys=True) != before
    write(data, changed)
    print("\n".join(report))
    print(f"changed={changed} last_date={data['last_date']}")


if __name__ == "__main__":
    main()
