// Run in a https://www.barchart.com tab (via Claude in Chrome's javascript tool).
// Fetches the last 10 daily closes for each symbol in SYMS and writes them into the
// page as plain lines "SYM,YYYY-MM-DD,close" so they can be read with get_page_text.
// Replace the SYMS list with the output of: python scripts/merge_update.py active
(async (SYMS) => {
  const xsrf = decodeURIComponent((document.cookie.match(/XSRF-TOKEN=([^;]+)/) || [])[1] || '');
  const lines = [];
  for (const s of SYMS) {
    const q = new URLSearchParams({symbol: s, data: 'daily', maxrecords: '1500', volume: 'contract', order: 'asc',
      dividends: 'false', backadjust: 'false', daystoexpiration: '1', contractroll: 'expiration'});
    const r = await fetch('/proxies/timeseries/queryeod.ashx?' + q, {headers: {'x-xsrf-token': xsrf}});
    const rows = (await r.text()).trim().split('\n').map(l => l.split(',')).filter(p => p[0] === s && p.length >= 6);
    lines.push(`# ${s} status=${r.status} rows=${rows.length}`);
    for (const p of rows.slice(-10)) lines.push(`${s},${p[1]},${p[5]}`);
  }
  document.title = 'sugar-update';
  document.body.innerHTML = '<article><pre id="sugar-update"></pre></article>';
  document.getElementById('sugar-update').textContent = lines.join('\n');
  return lines.filter(l => l.startsWith('#')).join(' | ');
})(["SBH27", "SBK27", "SBN27", "SWH27", "SWK27", "SWQ27"]);
