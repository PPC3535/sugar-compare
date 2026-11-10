import http.cookiejar
import urllib.request

H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/130.0 Safari/537.36",
     "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
for url in ["https://www.barchart.com/",
            "https://www.barchart.com/futures/quotes/SWH27/price-history/historical"]:
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        r = op.open(urllib.request.Request(url, headers=H), timeout=30)
        body = r.read(300).decode("utf-8", "replace")
        print("PROBE", url, r.status, [c.name for c in jar], repr(body[:160]))
    except Exception as e:
        print("PROBE", url, "ERR", e, repr(getattr(e, "read", lambda: b"")()[:160]))
