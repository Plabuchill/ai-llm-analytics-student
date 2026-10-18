// Checks the executive report: script syntax, words per section, and the PDF structure
// (xref offsets, stream lengths, invisible text layer). Writes out/report_preview.txt and out/test.pdf.
// Usage (from the repo root): node dashboard/checks/check_report.js
const fs = require('fs');
const path = require('path');
const page = process.argv[2] || path.resolve(__dirname, '..', 'index.html');
const outDir = path.resolve(__dirname, '..', 'out');
fs.mkdirSync(outDir, { recursive: true });
process.argv[3] = process.argv[3] || path.join(outDir, 'report_preview.txt');
process.argv[4] = process.argv[4] || path.join(outDir, 'test.pdf');
const s = fs.readFileSync(page, 'utf8');
const sc = [...s.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
sc.forEach((c, i) => { try { new Function(c); console.log('script', i, 'parses'); } catch (e) { console.log('script', i, e.message); } });
const src = sc[1];
const code = src.slice(src.indexOf('  const fmtN'), src.indexOf('  const downloadsPromise'));
global.d3 = { sum: (a, f) => a.reduce((t, x) => t + f(x), 0) };
global.root = { querySelector: () => ({}) };
let latestSummary = null;
eval(code + '; global.api = { fitReport, pagesToPdf, bulletText };');
const S = { ขอบเขตข้อมูล: 'ทุกภูมิภาค ทุกหมวด และทุกช่องทาง', ยอดขายสุทธิ_บาท: 14107737, คำสั่งซื้อสำเร็จ: 16249, AOV_บาท: 868.22, อัตรายกเลิก_ร้อยละ: 4.51, คำสั่งซื้อทั้งหมด: 17529, คำสั่งซื้อยกเลิก: 790, คำสั่งซื้อคืนสินค้า: 490, เดือนยอดสูงสุด: { เดือน: 'พ.ย. 2568', ยอดขาย_บาท: 1306940 }, เดือนยอดต่ำสุด: { เดือน: 'ก.พ. 2569', ยอดขาย_บาท: 962379 }, ช่องทางอันดับแรก: { ชื่อ: 'แอป', สัดส่วนยอดขาย_ร้อยละ: 39.76 }, ภูมิภาคอันดับแรก: { ชื่อ: 'กรุงเทพฯและปริมณฑล', สัดส่วนยอดขาย_ร้อยละ: 44.49 }, จังหวัดอันดับแรก: { ชื่อ: 'กรุงเทพมหานคร', สัดส่วนยอดขาย_ร้อยละ: 27.37 }, บริษัทขนส่งอันดับแรก: { ชื่อ: 'ไปไว Express', สัดส่วนยอดขาย_ร้อยละ: 41.14, ส่งเฉลี่ย_วัน: 3.29 }, วันเมกะเซล: { จำนวนวัน: 6, สัดส่วนยอดขาย_ร้อยละ: 3.44, ยอดขายเฉลี่ยต่อวัน_บาท: 80799, วันปกติยอดขายเฉลี่ยต่อวัน_บาท: 37947, กำไรขั้นต้น_ร้อยละ: 24.16, วันปกติกำไรขั้นต้น_ร้อยละ: 44.66, วันยอดสูงสุด: '11.11', วันยอดสูงสุดยอดขาย_บาท: 122718 } };
const r = api.fitReport(S);
let txt = '';
for (const sec of r.sections) { txt += `## ${sec.h} (${sec.words} words, ${sec.bullets.length} bullets)\n` + sec.bullets.map((b) => '- ' + api.bulletText(b)).join('\n') + '\n'; }
fs.writeFileSync(process.argv[3], txt);
console.log('total words', r.words);

// PDF structure with a stand-in page image
global.Blob = class { constructor(parts) { this.parts = parts; } };
const jpeg = Buffer.from('FFD8FFE000104A46494600010100000100010000FFD9', 'hex');
const fakeCanvas = { width: 1240, height: 1754, toBlob: (cb) => cb({ arrayBuffer: async () => jpeg.buffer.slice(jpeg.byteOffset, jpeg.byteOffset + jpeg.length) }) };
const pages = [{ canvas: fakeCanvas, runs: [{ str: 'บทสรุปผู้บริหาร', x: 110, y: 156, px: 52, w: 400 }, { str: 'ยอดขายสุทธิ ฿14,107,737 ที่', x: 150, y: 400, px: 26, w: 380 }] }, { canvas: fakeCanvas, runs: [{ str: 'หน้า 2/2', x: 1000, y: 1694, px: 20, w: 80 }] }];
api.pagesToPdf(pages).then((blob) => {
  const buf = Buffer.concat(blob.parts.map((p) => Buffer.from(p)));
  fs.writeFileSync(process.argv[4], buf);
  const str = buf.toString('latin1');
  const xrefAt = Number(str.match(/startxref\n(\d+)/)[1]);
  console.log('xref ok', str.slice(xrefAt, xrefAt + 4) === 'xref');
  const entries = str.slice(xrefAt).split('\n').slice(3).filter((l) => / n $/.test(l)).map((l) => Number(l.slice(0, 10)));
  const bad = entries.map((o, i) => [i + 1, str.slice(o, o + 12)]).filter(([n, t]) => !t.startsWith(`${n} 0 obj`));
  console.log('objects', entries.length, 'bad offsets', bad.length);
  const lens = [...str.matchAll(/\/Length (\d+) >>\nstream\n/g)];
  const badLen = lens.filter((m) => str.slice(m.index + m[0].length + Number(m[1]), m.index + m[0].length + Number(m[1]) + 10) !== '\nendstream');
  console.log('streams', lens.length, 'bad lengths', badLen.length);
  console.log(str.match(/BT [^\n]*/)[0].slice(0, 140));
});
