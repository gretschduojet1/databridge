import csv
import io

import pytest

from writers.excel import ExcelWriter
from writers.factory import get_writer
from writers.text import TextWriter

COLS = ["ID", "Name", "Value"]
ROWS = [(1, "Alice", 99.5), (2, "Bob", None)]


def test_text_writer_columns_and_rows() -> None:
    data = TextWriter().write(COLS, ROWS)
    text = data.decode("utf-8")
    lines = list(csv.reader(io.StringIO(text), delimiter="\t"))
    assert lines[0] == COLS
    assert lines[1] == ["1", "Alice", "99.5"]
    assert lines[2] == ["2", "Bob", ""]  # None → empty string


def test_text_writer_content_type() -> None:
    assert TextWriter().content_type == "text/plain"
    assert TextWriter().extension == "txt"


def test_excel_writer_returns_valid_xlsx() -> None:
    data = ExcelWriter().write(COLS, ROWS)
    assert isinstance(data, bytes)
    assert data[:2] == b"PK"  # xlsx is a zip file


def test_excel_writer_content_type() -> None:
    w = ExcelWriter()
    assert w.extension == "xlsx"
    assert "spreadsheetml" in w.content_type


def test_get_writer_xlsx() -> None:
    assert get_writer("xlsx").extension == "xlsx"


def test_get_writer_txt() -> None:
    assert get_writer("txt").extension == "txt"


def test_get_writer_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown format"):
        get_writer("pdf")
