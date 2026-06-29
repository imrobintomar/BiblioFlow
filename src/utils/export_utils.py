import csv
import io

from openpyxl import Workbook


def rows_to_csv(rows: list[dict], columns: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def rows_to_excel_bytes(rows: list[dict], columns: list[str]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(columns)
    for row in rows:
        ws.append([row.get(c, "") for c in columns])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
