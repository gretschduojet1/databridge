"""
Service bindings — the single place to swap implementations.

Equivalent to Laravel's AppServiceProvider::register(). Each function
is a FastAPI dependency: routes declare what they need via Depends(),
and this module decides which concrete class they get.

    # To switch the export writer to plain text:
    def get_export_writer() -> WriterProtocol:
        return TextWriter()
"""

from writers.interfaces.writer import WriterProtocol
from writers.excel import ExcelWriter


def get_export_writer() -> WriterProtocol:
    return ExcelWriter()
