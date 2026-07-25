from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


class InvalidCsvError(ValueError):
    """Raised when an uploaded file cannot be parsed as a usable CSV."""


@dataclass(frozen=True)
class CsvMetadata:
    rows: int
    columns: int


def inspect_csv(path: Path) -> CsvMetadata:
    """Validate a CSV file and return its basic dimensions."""
    parsing_errors: list[Exception] = []

    for encoding in ("utf-8-sig", "gb18030"):
        try:
            frame = pd.read_csv(path, encoding=encoding)
            if frame.shape[1] == 0:
                raise InvalidCsvError("CSV 文件没有可用列")
            return CsvMetadata(rows=int(frame.shape[0]), columns=int(frame.shape[1]))
        except UnicodeDecodeError as error:
            parsing_errors.append(error)
        except (EmptyDataError, ParserError) as error:
            raise InvalidCsvError("文件不是有效的 CSV，或文件内容为空") from error

    raise InvalidCsvError("CSV 编码不受支持，请使用 UTF-8 或 GB18030") from (
        parsing_errors[-1] if parsing_errors else None
    )
