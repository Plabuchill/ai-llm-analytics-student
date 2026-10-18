"""ฟังก์ชันคำนวณตัวชี้วัดของบ้านสบาย ช็อป

ทุกฟังก์ชันรับ DataFrame ที่ได้จาก load_orders() เป็นพารามิเตอร์แรก
นิยามตัวชี้วัดอยู่ใน CLAUDE.md
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

DELIVERED = "จัดส่งสำเร็จ"
CANCELLED = "ยกเลิก"
RETURNED = "คืนสินค้า"


def load_orders(path: Path | str = DATA / "orders.csv") -> pd.DataFrame:
    """อ่าน orders.csv แล้วเพิ่มคอลัมน์ที่ใช้บ่อย: net, unit_cost, gp, month, date

    net และ gp มีค่าเฉพาะแถวที่จัดส่งสำเร็จ แถวสถานะอื่นเป็น 0
    """
    orders = pd.read_csv(path, encoding="utf-8-sig")
    products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig", usecols=["product_id", "unit_cost"])
    df = orders.merge(products, on="product_id", how="left", validate="many_to_one")

    delivered = df["status"] == DELIVERED
    gross = df["qty"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    df["net"] = gross.where(delivered, 0.0)
    df["gp"] = (gross - df["qty"] * df["unit_cost"]).where(delivered, 0.0)
    df["month"] = df["order_datetime"].astype(str).str[:7]
    df["date"] = df["order_datetime"].astype(str).str[:10]
    return df


def _delivered(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == DELIVERED]


def _in_dates(df: pd.DataFrame, start_date: str | None, end_date: str | None) -> pd.Series:
    """แถวที่วันที่อยู่ในช่วง (รวมทั้งสองวัน) เทียบเป็นสตริง 'YYYY-MM-DD'"""
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= df["date"] >= start_date
    if end_date is not None:
        mask &= df["date"] <= end_date
    return mask


def _percent(part: float, whole: float) -> float:
    return float(part / whole * 100) if whole else 0.0


def net_sales(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิรวม (บาท)"""
    return float(_delivered(df)["net"].sum())


def gross_profit(df: pd.DataFrame) -> float:
    """กำไรขั้นต้นรวม (บาท)"""
    return float(_delivered(df)["gp"].sum())


def aov(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิเฉลี่ยต่อคำสั่งซื้อที่จัดส่งสำเร็จ (บาท)"""
    delivered = _delivered(df)
    orders = delivered["order_id"].nunique()
    return float(delivered["net"].sum() / orders) if orders else 0.0


def cancel_rate(df: pd.DataFrame) -> float:
    """อัตรายกเลิกของคำสั่งซื้อทั้งหมดใน df (เปอร์เซ็นต์ 0–100)"""
    return _percent((df["status"] == CANCELLED).sum(), len(df))


def monthly_sales(df: pd.DataFrame) -> pd.Series:
    """ยอดขายสุทธิรายเดือน index = 'YYYY-MM' เรียงตามเวลา"""
    return _delivered(df).groupby("month")["net"].sum().sort_index()


def best_month(df: pd.DataFrame) -> str:
    """เดือนที่ยอดขายสุทธิสูงสุด ('YYYY-MM')"""
    return str(monthly_sales(df).idxmax())


def channel_share(df: pd.DataFrame, channel: str, start_month: str, end_month: str) -> float:
    """สัดส่วนยอดขายสุทธิของช่องทางในช่วงเดือน start_month..end_month (รวมทั้งสองเดือน) เป็นเปอร์เซ็นต์"""
    delivered = _delivered(df)
    period = delivered[(delivered["month"] >= start_month) & (delivered["month"] <= end_month)]
    return _percent(period.loc[period["channel"] == channel, "net"].sum(), period["net"].sum())


def _ship_bucket(days: float) -> str:
    if days <= 2:
        return "1-2"
    if days <= 4:
        return "3-4"
    if days <= 6:
        return "5-6"
    return "7+"


def rating_by_ship_bucket(df: pd.DataFrame) -> dict[str, float]:
    """คะแนนรีวิวเฉลี่ยตามระยะส่ง คืน dict คีย์ '1-2', '3-4', '5-6', '7+'

    ใช้ทุกแถวที่มีทั้ง rating และ ship_days (ตัดค่าว่างก่อนเฉลี่ย)
    """
    rated = df.dropna(subset=["rating", "ship_days"])
    means = rated.groupby(rated["ship_days"].map(_ship_bucket))["rating"].mean()
    return {bucket: float(means[bucket]) for bucket in ["1-2", "3-4", "5-6", "7+"] if bucket in means}


def top_province(df: pd.DataFrame, region: str) -> str:
    """จังหวัดที่มียอดขายสุทธิสูงสุดในภูมิภาคที่ระบุ"""
    delivered = _delivered(df)
    by_province = delivered[delivered["region"] == region].groupby("province")["net"].sum()
    return str(by_province.idxmax())


def avg_ship_days(df: pd.DataFrame, region: str | None = None, carrier: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> float:
    """ระยะส่งเฉลี่ย (วัน) ตามตัวกรองที่ให้มา วันที่เป็น 'YYYY-MM-DD' และรวมทั้งสองวัน

    ใช้ทุกแถวที่มี ship_days (คำสั่งซื้อที่ยกเลิกไม่มีค่านี้จึงถูกตัดออก)
    """
    mask = _in_dates(df, start_date, end_date) & df["ship_days"].notna()
    if region is not None:
        mask &= df["region"] == region
    if carrier is not None:
        mask &= df["carrier"] == carrier
    return float(df.loc[mask, "ship_days"].mean())


def month_orders(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """คำสั่งซื้อทุกสถานะของเดือน 'YYYY-MM'"""
    return df[df["month"] == month]


def previous_month(month: str) -> str:
    """เดือนก่อนหน้าของ 'YYYY-MM'"""
    return (pd.Period(month, freq="M") - 1).strftime("%Y-%m")


def top_products(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """สินค้าที่ยอดขายสุทธิสูงสุด n อันดับ คอลัมน์ product_id, product_name, qty, net"""
    return (_delivered(df)
            .groupby(["product_id", "product_name"], as_index=False)[["qty", "net"]].sum()
            .sort_values(["net", "product_id"], ascending=[False, True])
            .head(n)
            .reset_index(drop=True))


def return_rate(df: pd.DataFrame, product_id: str | None = None,
                start_date: str | None = None, end_date: str | None = None) -> float:
    """อัตราคืนสินค้า (เปอร์เซ็นต์) ของสินค้าและช่วงวันที่ที่ระบุ

    ตัวหารคือคำสั่งซื้อทั้งหมดในกลุ่ม (ทุกสถานะ) ตามนิยามใน CLAUDE.md
    """
    mask = _in_dates(df, start_date, end_date)
    if product_id is not None:
        mask &= df["product_id"] == product_id
    group = df[mask]
    return _percent((group["status"] == RETURNED).sum(), len(group))
