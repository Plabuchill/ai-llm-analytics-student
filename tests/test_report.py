"""รายงานรายเดือนจาก src/report.py"""
import pytest

from src import metrics as m
from src import report


@pytest.fixture(scope="module")
def df():
    return m.load_orders()


def test_report_march_net_sales(df):
    text = report.build_report(df, "2026-03")
    assert "| ยอดขายสุทธิ | ฿1,147,155 |" in text


def test_report_sections(df):
    text = report.build_report(df, "2026-03")
    assert "เทียบเดือนก่อน (2026-02)" in text
    assert "อัตรายกเลิก" in text and "อัตราคืนสินค้า" in text
    for rank in range(1, 6):
        assert f"\n| {rank} | " in text


def test_write_report_file(df, tmp_path):
    out = report.write_report("2026-03", tmp_path / "monthly_report.md", df=df)
    assert out.exists()
    assert "฿1,147,155" in out.read_text(encoding="utf-8")


def test_report_unknown_month(df):
    with pytest.raises(ValueError):
        report.build_report(df, "2030-01")
