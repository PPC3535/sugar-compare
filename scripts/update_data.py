#!/usr/bin/env python3
"""Fetch daily settlement prices for sugar futures from Barchart and write
data/data.json (compact, used by index.html) and data/sugar_daily.csv.

Contracts that fail to download keep their previous data, so a partial
outage never wipes the site. Exits non-zero only if *nothing* could be fetched.
"""
import csv, datetime as dt, http.cookiejar, json, os, sys, time, urllib.parse, urllib.request

FAMILIES = ["SWH", "SWK", "SWQ", "SBH", "SBK", "SBN"]
YEARS = ["24", "25", "26", "27"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "data", "data.json")
CSV_PATH = os.path.join(ROOT, "data", "sugar_daily.csv")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

def scale(sym):
    return 100 if sym.startswith("SB") else 10

def session():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        "https://www.barchart.com/futures/quotes/SWH27/price-history/historical",
        headers={"User-Agent": UA, "Accept": "text/html"})
    opener.open(req, timeout=30).read()
    token = next((urllib.parse.unquote(c.value) for c in jar if c.name == "XSRF-TOKEN"), None)
    if not token:
        raise RuntimeError("no XSRF-TOKEN cookie from barchart")
    return opener, token

def fetch(opener, token, sym):
    q = urllib.parse.urlencode({
        "symbol": sym, "data": "daily", "maxrecords": 1500, "volume": "contract",
        "order": "asc", "dividends": "false", "backadjust": "false",
        "daystoexpiration": 1, "contractroll": "expiration"})
    req = urllib.request.Request(
        "https://www.barchart.com/proxies/timeseries/queryeod.ashx?" + q,
        headers={"User-Agent": UA, "x-xsrf-token": token, "Accept": "*/*",
                 "Referer": f"https://www.barchart.com/futures/quotes/{sym}/price-history/historical"})
    text = opener.open(req, timeout=30).read().decode("utf-8").strip()
    rows = []
    for line in text.splitlines():
        p = line.split(",")
        if len(p) >= 6 and p[0] == sym:
            dt.date.fromisoformat(p[1])
            rows.append((p[1], float(p[5])))
    if len(rows) < 20:
        raise RuntimeError(f"{sym}: only {len(rows)} rows")
    return rows

def encode(sym, rows):
    sc = scale(sym)
    start = dt.date.fromisoformat(rows[0][0])
    prev, gaps, closes = start, [], []
    for d, c in rows:
        dd = dt.date.fromisoformat(d)
        gaps.append((dd - prev).days)
        prev = dd
        closes.append(round(c * sc))
    return [rows[0][0], gaps, closes]

def decode(sym, packed):
    start, gaps, closes = packed
    d = dt.date.fromisoformat(start)
    out = []
    for g, c in zip(gaps, closes):
        d += dt.timedelta(days=g)
        out.append((d.isoformat(), c / scale(sym)))
    return out

def main():
    old = {}
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH) as f:
            old = json.load(f).get("symbols", {})
    opener, token = session()
    symbols, ok, failed = {}, [], []
    for fam in FAMILIES:
        for yy in YEARS:
            sym = fam + yy
            try:
                rows = fetch(opener, token, sym)
                prev_last = decode(sym, old[sym])[-1][0] if sym in old else ""
                if rows[-1][0] < prev_last:
                    raise RuntimeError(f"{sym}: new data ends {rows[-1][0]} before old {prev_last}")
                symbols[sym] = encode(sym, rows)
                ok.append(sym)
            except Exception as e:  # keep old data for this contract
                failed.append(f"{sym}: {e}")
                if sym in old:
                    symbols[sym] = old[sym]
            time.sleep(0.6)
    if not ok:
        print("Nothing fetched:\n" + "\n".join(failed), file=sys.stderr)
        sys.exit(1)
    last = max(decode(s, p)[-1][0] for s, p in symbols.items())
    changed = symbols != old
    payload = {"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if changed else None,
               "last_date": last, "symbols": symbols}
    if not changed and os.path.exists(JSON_PATH):
        with open(JSON_PATH) as f:
            payload["generated"] = json.load(f).get("generated")
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["contract", "date", "close"])
        for sym in sorted(symbols):
            for d, c in decode(sym, symbols[sym]):
                w.writerow([sym, d, c])
    print(f"fetched {len(ok)}/{len(FAMILIES) * len(YEARS)} contracts, latest date {last}, changed={changed}")
    for msg in failed:
        print("WARN", msg)

if __name__ == "__main__":
    main()
