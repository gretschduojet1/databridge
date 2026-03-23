import io

import openpyxl


class ExcelWriter:
    extension = "xlsx"
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def write(self, columns: list[str], rows: list) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(columns)
        for row in rows:
            ws.append([v.replace(tzinfo=None) if hasattr(v, "tzinfo") and v.tzinfo else v for v in row])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
