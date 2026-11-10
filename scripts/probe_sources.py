import json
import urllib.request

H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/130.0 Safari/537.36"}
for sym in ["SBH27.NYB", "SBK27.NYB", "SBN27.NYB", "SB=F"]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d"
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30)
        j = json.load(r)
        res = j["chart"]["result"][0]
        closes = res["indicators"]["quote"][0]["close"]
        print("PROBE", sym, r.status, len(res.get("timestamp") or []), closes[-3:])
    except Exception as e:
        print("PROBE", sym, "ERR", e)
