// Runs the dashboard's calculations on the CSV files and prints the totals to compare with Python.
// Usage (from the repo root): node dashboard/checks/check_calcs.js [page] [orders.csv] [products.csv]
const fs = require('fs');
const path = require('path');
const repo = path.resolve(__dirname, '..', '..');
const page = process.argv[2] || path.join(repo, 'dashboard', 'index.html');
const ordersPath = process.argv[3] || path.join(repo, 'data', 'orders.csv');
const productsPath = process.argv[4] || path.join(repo, 'data', 'products.csv');
const s = fs.readFileSync(page, 'utf8').split('\r\n').join('\n');
const calcs = {};
global.dash = { calc: (id, def) => { calcs[id] = def; } };
const first = s.indexOf('<script>') + 8;
eval(s.slice(first, s.indexOf('</script>', first)));

function parse(t) {
  t = t.replace(/^﻿/, '﻿');
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (q) { if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n') { row.push(f.replace(/\r$/, '')); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const h = rows.shift();
  return rows.filter((r) => r.length === h.length).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i]])));
}
const data = { orders: parse(fs.readFileSync(ordersPath, 'utf8')), products: parse(fs.readFileSync(productsPath, 'utf8')) };
const out = {};
for (const [id, def] of Object.entries(calcs)) out[id] = def.fn(...def.inputs.map((i) => data[i]));
const sum = (a, f) => a.reduce((t, x) => t + f(x), 0);
const ok = out.cube.filter((r) => r.status === 'จัดส่งสำเร็จ' && r.valid);
console.log('cube rows', out.cube.length, 'orders', sum(out.cube, (r) => r.orders), 'net', Math.round(sum(ok, (r) => r.net)), 'okOrders', sum(ok, (r) => r.orders));
console.log('carrier rows', out.by_carrier.length, 'net', Math.round(sum(out.by_carrier, (r) => r.net)));
console.log('province rows', out.by_province.length, 'net', Math.round(sum(out.by_province, (r) => r.net)));
const m = out.mega.filter((r) => r.kind === 'mega'), n = out.mega.filter((r) => r.kind === 'normal');
const mn = sum(m, (r) => r.net), nn = sum(n, (r) => r.net);
console.log('mega rows', out.mega.length, 'megaNet', Math.round(mn), 'margin', ((mn - sum(m, (r) => r.cost)) / mn * 100).toFixed(2), 'normalMargin', ((nn - sum(n, (r) => r.cost)) / nn * 100).toFixed(2));
const dates = [...new Set(out.cube.filter((r) => r.valid).map((r) => r.date))].sort();
console.log('days', dates.length, dates[0], dates[dates.length - 1]);
const q4 = ok.filter((r) => r.date >= '2025-10-01' && r.date <= '2025-12-31' && r.channel === 'แอป');
console.log('Q4 app net', Math.round(sum(q4, (r) => r.net)), 'orders', sum(q4, (r) => r.orders));
console.log('json bytes', JSON.stringify(out.cube).length, JSON.stringify(out.by_carrier).length, JSON.stringify(out.by_province).length, JSON.stringify(out.mega).length);
