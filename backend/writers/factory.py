from writers.excel import ExcelWriter
from writers.interfaces.writer import WriterProtocol
from writers.text import TextWriter

_registry: dict[str, WriterProtocol] = {
    "xlsx": ExcelWriter(),
    "txt": TextWriter(),
}


def get_writer(fmt: str = "xlsx") -> WriterProtocol:
    writer = _registry.get(fmt)
    if not writer:
        raise ValueError(f"Unknown format '{fmt}'. Available: {list(_registry)}")
    return writer
