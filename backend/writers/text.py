import csv
import io


class TextWriter:
    extension = "txt"
    content_type = "text/plain"

    def write(self, columns: list[str], rows: list) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter="\t")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([str(v) if v is not None else "" for v in row])
        return buf.getvalue().encode("utf-8")
