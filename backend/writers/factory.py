from writers.excel import ExcelWriter
from writers.text import TextWriter
from writers.interfaces.writer import WriterProtocol

_registry: dict[str, WriterProtocol] = {
    "xlsx": ExcelWriter(),
    "txt":  TextWriter(),
}


def get_writer(fmt: str = "xlsx") -> WriterProtocol:
    writer = _registry.get(fmt)
    if not writer:
        raise ValueError(f"Unknown format '{fmt}'. Available: {list(_registry)}")
    return writer
