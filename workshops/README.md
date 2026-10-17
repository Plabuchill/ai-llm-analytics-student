# งานเวิร์กช็อปคาบ 1–2

## W1 · LLM กับงานตัวเลข
- `w1/w1b_analysis.py` ยอดขายสุทธิ กำไรขั้นต้น AOV ยอดรายเดือน และสัดส่วนช่องทาง ไตรมาส ต.ค.–ธ.ค. 2025 เทียบ ก.ค.–ก.ย. 2026
  รัน: `python workshops/w1/w1b_analysis.py` → `w1/outputs/w1b_summary.xlsx`, `w1/outputs/w1b_monthly_sales.png`

## W2 · Prompt และการวัดความแม่น
- `w2/outputs/prompts/classify_v2.md`, `classify_v3.md` prompt จัดหมวด ticket
- `w2/outputs/w2a_pred_*.csv` ผลทำนาย v1/v2/v3 (dev) และ v3 (test) · `*_errors.csv` แถวที่ผิด
- `w2/w2a_eval.py` วัด accuracy, recall ของ urgency=สูง, confusion matrix
  รัน: `python workshops/w2/w2a_eval.py <pred.csv> <gold.csv> <tickets.csv>`
  (ไฟล์ `tickets_dev*.csv` / `tickets_test.csv` อยู่ในชุดผู้เรียน ไม่ได้อยู่ใน repo นี้)

| เวอร์ชัน | ชุด | category | sentiment | urgency | ถูกครบ 3 |
|---|---|---|---|---|---|
| v1 | dev 150 | 100% | 86.0% | 89.3% | 79.3% |
| v2 / v3 | dev 150 | 100% | 100% | 100% | 100% |
| v3 | test 100 | 99.0% | 99.0% | 98.0% | 96.0% |
