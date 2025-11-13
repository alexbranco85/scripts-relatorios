#!/usr/bin/env python3
"""Gera um CSV de relatório SMS a partir de um CSV com telefones."""
#!/usr/bin/env python3
# """
# Requisitos opcionais:
#   python3 -m venv .venv
#   source .venv/bin/activate
#   python -m pip install aiohttp tqdm
# """


# SELECT 
#        l.phone
# FROM leads l
# WHERE l.deleted_at IS NULL
#   AND l.active = 1
#   AND l.id IN (
#     SELECT llm.lead_id
#     FROM leads_lists_map llm
#     WHERE llm.lead_list_id IN (
#       SELECT ahl.lead_list_id
#       FROM actions_has_lists ahl
#       WHERE ahl.actions_id = 1839803
#     )
#   )
# GROUP BY l.phone
# ORDER BY l.phone
# LIMIT 15000 OFFSET 0;

import csv
from pathlib import Path
from typing import Iterable, Tuple

# ==============================
# CONFIGURAÇÕES
# ==============================

# Caminho do CSV de entrada (primeira coluna com os telefones).
ARQUIVO_CSV = Path("telefones.csv")

# Caminho do CSV que será criado.
ARQUIVO_CSV_SAIDA = Path("relatorio_sms_1839803.csv")

# Valores fixos para as colunas "Data" e "Hora".
DATA_ENVIO = "31/10/2025"  # formato brasileiro
HORA_ENVIO = "17:04:00 AM"

# Se o CSV possui cabeçalho na primeira linha, defina como True.
IGNORAR_HEADER = True

# ==============================


def _normalizar_destino(valor: str) -> str:
    digitos = "".join(ch for ch in valor if ch.isdigit())
    if not digitos:
        raise ValueError("Telefone vazio após normalização.")
    if digitos.startswith("55"):
        return digitos
    return f"55{digitos}"


def _carregar_telefones(caminho_csv: Path) -> Iterable[Tuple[int, str]]:
    with caminho_csv.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        for indice_linha, linha in enumerate(leitor, start=1):
            if indice_linha == 1 and IGNORAR_HEADER:
                continue
            if not linha:
                continue
            telefone = linha[0].strip()
            if not telefone:
                continue
            yield indice_linha, telefone


def gerar_relatorio_sms():
    if not ARQUIVO_CSV.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {ARQUIVO_CSV}")

    total = 0
    with ARQUIVO_CSV_SAIDA.open("w", encoding="utf-8", newline="") as arquivo_saida:
        escritor = csv.writer(arquivo_saida)
        escritor.writerow(("Destino", "Status", "Data", "Hora"))

        for numero_linha, telefone in _carregar_telefones(ARQUIVO_CSV):
            try:
                destino = _normalizar_destino(telefone)
            except ValueError as exc:
                raise ValueError(f"Erro na linha {numero_linha}: {exc}") from exc

            escritor.writerow((destino, "Enviada", DATA_ENVIO, HORA_ENVIO))
            total += 1

    print(f"✅ Relatório criado ({total} registros) → {ARQUIVO_CSV_SAIDA.resolve()}")


if __name__ == "__main__":
    gerar_relatorio_sms()
