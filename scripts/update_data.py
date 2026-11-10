#!/usr/bin/env python3
"""Fetch daily settlement prices for sugar futures from Barchart and write
data/data.json (compact, used by index.html) and data/sugar_daily.csv.

Contracts that fail to download keep their previous data, so a partial
outage never wipes the site. Exits non-zero only if *nothing* could be fetched.
"""
import csv, datetime as dt, json, os, sys

FAMILIES = ["SWH", "SWK", "SWQ", "SBH", "SBK", "SBN"]
YEARS = ["24", "25", "26", "27"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "data", "data.json")
CSV_PATH = os.path.join(ROOT, "data", "sugar_daily.csv")

def scale(sym):
    return 100 if sym.startswith("SB") else 10

def fetch_all(symbols):
    """Open Barchart in headless Chromium (it blocks plain HTTP clients with a
    bot check), then call its chart-data endpoint from inside the page."""
    from playwright.sync_api import sync_playwright
    results, errors = {}, {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="en-US")
        page.goto("https://www.barchart.com/futures/quotes/SWH27/price-history/historical",
                  wait_until="domcontentloaded", timeout=90000)
        for _ in range(30):  # wait for the bot check to clear and the token cookie to appear
            if page.evaluate("document.cookie.includes('XSRF-TOKEN')"):
                break
            page.wait_for_timeout(2000)
        else:
            raise RuntimeError("no XSRF-TOKEN cookie after waiting; title=%r" % page.title())
        for sym in symbols:
            try:
                text = page.evaluate("""async (sym) => {
                    const xsrf = decodeURIComponent((document.cookie.match(/XSRF-TOKEN=([^;]+)/) || [])[1] || '');
                    const q = new URLSearchParams({symbol: sym, data: 'daily', maxrecords: '1500', volume: 'contract',
                      order: 'asc', dividends: 'false', backadjust: 'false', daystoexpiration: '1', contractroll: 'expiration'});
                    const r = await fetch('/proxies/timeseries/queryeod.ashx?' + q, {headers: {'x-xsrf-token': xsrf}});
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return await r.text();
                }""", sym)
                rows = []
                for line in text.strip().splitlines():
                    f = line.split(",")
                    if len(f) >= 6 and f[0] == sym:
                        dt.date.fromisoformat(f[1])
                        rows.append((f[1], float(f[5])))
                if len(rows) < 20:
                    raise RuntimeError(f"only {len(rows)} rows")
                results[sym] = rows
            except Exception as e:
                errors[sym] = str(e)
            page.wait_for_timeout(500)
        browser.close()
    return results, errors

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
    wanted = [fam + yy for fam in FAMILIES for yy in YEARS]
    fetched, errors = fetch_all(wanted)
    symbols, ok, failed = {}, [], []
    for sym in wanted:
        try:
            if sym not in fetched:
                raise RuntimeError(errors.get(sym, "not fetched"))
            rows = fetched[sym]
            prev_last = decode(sym, old[sym])[-1][0] if sym in old else ""
            if rows[-1][0] < prev_last:
                raise RuntimeError(f"new data ends {rows[-1][0]} before old {prev_last}")
            symbols[sym] = encode(sym, rows)
            ok.append(sym)
        except Exception as e:  # keep old data for this contract
            failed.append(f"{sym}: {e}")
            if sym in old:
                symbols[sym] = old[sym]
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
