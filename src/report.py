"""สร้างรายงานยอดขายรายเดือนเป็น Markdown

ใช้งาน: python -m src.report 2026-03
ตัวเลขทุกตัวคำนวณด้วยฟังก์ชันใน src/metrics.py
"""
import argparse
import re
from pathlib import Path

import pandas as pd

from src import metrics as m

REPORTS = Path(__file__).resolve().parent.parent / "reports"


def _baht(value: float) -> str:
    return f"฿{value:,.0f}"


def _change(current: float, previous: float) -> str:
    if not previous:
        return "—"
    pct = (current - previous) / previous * 100
    return f"{pct:+.2f}%"


def build_report(df: pd.DataFrame, month: str) -> str:
    """เนื้อหารายงาน Markdown ของเดือน 'YYYY-MM'"""
    month_df = m.month_orders(df, month)
    if month_df.empty:
        raise ValueError(f"ไม่มีคำสั่งซื้อในเดือน {month}")

    prev = m.previous_month(month)
    prev_df = m.month_orders(df, prev)
    net = m.net_sales(month_df)
    lines = [
        f"# รายงานยอดขายรายเดือน {month}",
        "",
        "บ้านสบาย ช็อป · ยอดขายสุทธินับเฉพาะคำสั่งซื้อที่จัดส่งสำเร็จ ไม่รวมค่าจัดส่ง",
        "",
        "## สรุป",
        "",
        "| ตัวชี้วัด | ค่า |",
        "|---|---|",
        f"| ยอดขายสุทธิ | {_baht(net)} |",
    ]
    if prev_df.empty:
        lines.append(f"| เทียบเดือนก่อน ({prev}) | ไม่มีข้อมูลเดือนก่อน |")
    else:
        prev_net = m.net_sales(prev_df)
        lines.append(f"| เทียบเดือนก่อน ({prev}) | {_baht(prev_net)} → {_change(net, prev_net)} |")
    lines += [
        f"| อัตรายกเลิก | {m.cancel_rate(month_df):.2f}% |",
        f"| อัตราคืนสินค้า | {m.return_rate(month_df):.2f}% |",
        "",
        "## 5 สินค้าขายดี",
        "",
        "| อันดับ | สินค้า | จำนวน (ชิ้น) | ยอดขายสุทธิ |",
        "|---|---|---|---|",
    ]
    for rank, row in enumerate(m.top_products(month_df, 5).itertuples(index=False), start=1):
        lines.append(f"| {rank} | {row.product_name} ({row.product_id}) | {int(row.qty):,} | {_baht(row.net)} |")
    lines.append("")
    return "\n".join(lines)


def write_report(month: str, out: Path | str = REPORTS / "monthly_report.md", df: pd.DataFrame | None = None) -> Path:
    """เขียนรายงานของเดือนลงไฟล์ แล้วคืน path ของไฟล์"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_report(m.load_orders() if df is None else df, month), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="สร้างรายงานยอดขายรายเดือน")
    parser.add_argument("month", help="เดือนในรูปแบบ YYYY-MM เช่น 2026-03")
    parser.add_argument("--out", default=str(REPORTS / "monthly_report.md"), help="ไฟล์ปลายทาง")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
        parser.error("เดือนต้องอยู่ในรูปแบบ YYYY-MM")
    print(f"เขียนรายงานแล้ว: {write_report(args.month, args.out)}")


if __name__ == "__main__":
    main()
