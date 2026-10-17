"""วัดผลการจัดหมวด ticket เทียบกับ gold
ใช้: python w2a_eval.py outputs/w2a_pred_v1.csv data/tickets_dev_gold.csv data/tickets_dev.csv
"""
import sys

import pandas as pd

pred_path, gold_path, text_path = sys.argv[1:4]
FIELDS = ["category", "sentiment", "urgency"]

pred = pd.read_csv(pred_path, encoding="utf-8-sig")
gold = pd.read_csv(gold_path, encoding="utf-8-sig")
text = pd.read_csv(text_path, encoding="utf-8-sig")[["ticket_id", "message"]]
for d in (pred, gold):
    d.columns = d.columns.str.strip()
    for c in FIELDS:
        d[c] = d[c].astype(str).str.strip()

print("pred:", pred.shape, " gold:", gold.shape)
print("คอลัมน์ gold:", list(gold.columns))
missing = set(gold.ticket_id) - set(pred.ticket_id)
extra = set(pred.ticket_id) - set(gold.ticket_id)
print("ไม่มีใน pred:", len(missing), " เกินมาใน pred:", len(extra))

m = gold[["ticket_id"] + FIELDS].merge(pred[["ticket_id"] + FIELDS], on="ticket_id", suffixes=("_gold", "_pred"))
m = m.merge(text, on="ticket_id", how="left")
if "note" in gold.columns:
    m = m.merge(gold[["ticket_id", "note"]], on="ticket_id", how="left")
print("จับคู่ได้:", len(m), "แถว\n")

print("Accuracy")
for c in FIELDS:
    acc = (m[f"{c}_gold"] == m[f"{c}_pred"]).mean()
    print(f"  {c:<10} {acc:6.1%}  ({(m[f'{c}_gold'] == m[f'{c}_pred']).sum()}/{len(m)})")
all3 = (m[[f"{c}_gold" for c in FIELDS]].values == m[[f"{c}_pred" for c in FIELDS]].values).all(axis=1)
print(f"  {'ถูกทั้ง 3':<10} {all3.mean():6.1%}")

# urgency=สูง พลาดแล้วแพงกว่า จึงดู recall/precision แยก
hi_g, hi_p = m["urgency_gold"] == "สูง", m["urgency_pred"] == "สูง"
print(f"\nurgency=สูง  recall {(hi_g & hi_p).sum()}/{hi_g.sum()}  precision {(hi_g & hi_p).sum()}/{hi_p.sum()}")

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 20)
print("\nConfusion matrix ของ category (แถว = gold, คอลัมน์ = pred)")
cm = pd.crosstab(m["category_gold"], m["category_pred"], margins=True, margins_name="รวม")
print(cm.to_string())

print("\nความแม่นรายหมวด (recall ต่อหมวดใน gold)")
per = (m["category_gold"] == m["category_pred"]).groupby(m["category_gold"]).mean()
print(per.sort_values().map("{:.0%}".format).to_string())

# แถวที่ผิดอย่างน้อย 1 ฟิลด์ เรียงให้ category ผิดขึ้นก่อน
m["errors"] = m.apply(
    lambda r: ", ".join(f"{c}: {r[c + '_gold']}→{r[c + '_pred']}" for c in FIELDS if r[c + "_gold"] != r[c + "_pred"]),
    axis=1,
)
wrong = m[m["errors"] != ""].assign(cat_ok=lambda d: d.category_gold == d.category_pred).sort_values("cat_ok", kind="stable")
print(f"\nแถวที่ผิดอย่างน้อย 1 ฟิลด์: {len(wrong)} แถว (category ผิด {(~wrong.cat_ok).sum()}) · แสดง 10 แถวแรก (gold→pred)")
for r in wrong.head(10).itertuples():
    note = f"  [note: {r.note}]" if "note" in m and pd.notna(r.note) else ""
    print(f"- {r.ticket_id} {r.errors}{note}\n    {r.message}")
wrong[["ticket_id", "errors", "message"]].to_csv(pred_path.replace(".csv", "_errors.csv"), index=False, encoding="utf-8-sig")

for c in ["sentiment", "urgency"]:
    print(f"\n{c} (แถว = gold, คอลัมน์ = pred)")
    print(pd.crosstab(m[f"{c}_gold"], m[f"{c}_pred"]).to_string())
