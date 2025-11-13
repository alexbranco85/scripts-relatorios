"""Utility script to remove duplicated ``sid`` entries from an Excel workbook.

Como executar:
    python remove-sid-duplicado.py caminho/arquivo.xlsx [-o saida.xlsx] [-c coluna]

Parâmetros:
    input_file (obrigatório): caminho para o arquivo .xlsx a ser processado.
    --output / -o (opcional): caminho para o novo arquivo sem duplicados.
    --column / -c (opcional): coluna usada para identificar duplicidades (padrão: 'sid').
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit(
        "Dependencia ausente: instale 'pandas' (ex.: pip install pandas openpyxl)"
    ) from exc


def remove_duplicates(input_path: Path, output_path: Path, column: str = "sid") -> int:
    """Remove duplicated rows based on the target column and persist a new workbook."""
    df = pd.read_excel(input_path)

    if column not in df.columns:
        available = ", ".join(df.columns)
        raise ValueError(f"Coluna '{column}' não encontrada. Colunas disponíveis: {available}")

    original_len = len(df)
    cleaned_df = df.drop_duplicates(subset=[column], keep="first")
    cleaned_df.to_excel(output_path, index=False)

    return original_len - len(cleaned_df)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove registros duplicados de um arquivo Excel considerando a coluna 'sid'."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Caminho para o arquivo .xlsx que contém os dados.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Caminho opcional para o arquivo limpo (.xlsx).",
    )
    parser.add_argument(
        "-c",
        "--column",
        default="sid",
        help="Nome da coluna usada para identificar duplicidades. Padrão: 'sid'.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path: Path = args.input_file
    if not input_path.suffix:
        input_path = input_path.with_suffix(".xlsx")

    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")

    output_path: Path
    if args.output is not None:
        output_path = args.output
        if not output_path.suffix:
            output_path = output_path.with_suffix(".xlsx")
    else:
        output_path = input_path.with_name(f"{input_path.stem}_sem_sid_duplicado.xlsx")

    removed_count = remove_duplicates(input_path, output_path, args.column)

    print(
        f"Arquivo '{output_path.name}' criado com sucesso. "
        f"Registros removidos pela coluna '{args.column}': {removed_count}."
    )


if __name__ == "__main__":
    main()
