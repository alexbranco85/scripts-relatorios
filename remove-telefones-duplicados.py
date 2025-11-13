"""Utility script to remove duplicated phone entries from an Excel workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit(
        "Dependencia ausente: instale 'pandas' (ex.: pip install pandas openpyxl)"
    ) from exc


def remove_duplicates(input_path: Path, output_path: Path, column: str = "To") -> int:
    """Remove duplicated rows based on the target column and persist a new workbook.

    Returns the number of rows dropped so the caller can log the result.
    """
    df = pd.read_excel(input_path)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available columns: {list(df.columns)}")

    original_len = len(df)
    cleaned_df = df.drop_duplicates(subset=[column], keep="first")
    cleaned_df.to_excel(output_path, index=False)

    return original_len - len(cleaned_df)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove duplicated records from an Excel file using a chosen column."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the .xlsx file that contains the data.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path for the cleaned .xlsx file.",
    )
    parser.add_argument(
        "-c",
        "--column",
        default="To",
        help="Column name used to identify duplicated rows. Defaults to 'To'.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path: Path = args.input_file
    if not input_path.suffix:
        input_path = input_path.with_suffix(".xlsx")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path: Path
    if args.output is not None:
        output_path = args.output
        if not output_path.suffix:
            output_path = output_path.with_suffix(".xlsx")
    else:
        output_path = input_path.with_name(f"{input_path.stem}_sem_duplicados.xlsx")

    removed_count = remove_duplicates(input_path, output_path, args.column)

    print(
        f"Arquivo '{output_path.name}' criado com sucesso. "
        f"Registros removidos pela coluna '{args.column}': {removed_count}."
    )


if __name__ == "__main__":
    main()
