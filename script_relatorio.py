#!/usr/bin/env python3
"""
Script para disparar requisições POST para /v1/sms individualmente.

Requisitos opcionais:
  python3 -m venv .venv && source .venv/bin/activate
  python -m pip install aiohttp tqdm
"""

#!/usr/bin/env python3
import datetime
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from openpyxl import Workbook
from twilio.rest import Client

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    ZoneInfo = None
    ZoneInfoNotFoundError = None

# ==============================
# CONFIGURAÇÕES - ALTERE AQUI 👇
# ==============================

# Período de datas que você quer puxar (formato YYYY-MM-DD)
DATA_INICIO = "2025-11-11"
DATA_FIM = "2025-11-11"

# Texto que deseja filtrar nas mensagens (case-insensitive).
# Se não quiser filtro, deixe vazio: FILTRO = ""
# Para usar regex, defina USAR_REGEX = True
FILTRO = r"NOVO SLOT DISPONIVEL!!! MYSTIC WISHES da Pragmatic"
USAR_REGEX = True

# Nome do arquivo XLSX de saída
ARQUIVO_SAIDA = "relatorio-hiper.xlsx"

# Quantidade de blocos/threads simultâneas para as requisições
NUM_WORKERS = 300

# Credenciais padrão do Twilio (podem ser sobrescritas via env ou parâmetros)
DEFAULT_ACCOUNT_SID = ""
DEFAULT_AUTH_TOKEN = ""

ENV_CREDENTIAL_KEYS = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")


def _tem_credenciais_configuradas() -> bool:
    return all(os.getenv(chave) for chave in ENV_CREDENTIAL_KEYS)


def carregar_credenciais_twilio():
    """
    Preenche as variáveis de ambiente do Twilio lendo arquivos .env próximos ao script
    (ou ao executável empacotado). Ajuda quando o usuário executa o .exe com duplo clique.
    """
    if _tem_credenciais_configuradas():
        return

    candidatos: List[Path] = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(sys.executable).resolve().parent)

    try:
        script_dir = Path(__file__).resolve().parent
        candidatos.append(script_dir)
    except NameError:
        pass

    candidatos.append(Path.cwd())

    arquivos = [".env", "twilio.env", "twilio_credentials.env"]
    visitados = set()

    for base in candidatos:
        for nome in arquivos:
            caminho = (base / nome).resolve()
            if caminho in visitados or not caminho.is_file():
                continue
            visitados.add(caminho)

            try:
                linhas = caminho.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue

            for linha in linhas:
                conteudo = linha.strip()
                if not conteudo or conteudo.startswith("#") or "=" not in conteudo:
                    continue
                chave, valor = conteudo.split("=", 1)
                chave = chave.replace("export", "", 1).strip()
                valor = valor.strip().strip('"').strip("'")
                if chave in ENV_CREDENTIAL_KEYS and not os.getenv(chave):
                    os.environ[chave] = valor

            if _tem_credenciais_configuradas():
                return


carregar_credenciais_twilio()

# ==============================
# FIM DAS CONFIGURAÇÕES
# ==============================

def obter_fuso_brasil() -> datetime.tzinfo:
    """
    Retorna o fuso horário de São Paulo mesmo quando o tzdata não está disponível
    (ex.: Windows sem pacote tzdata instalado). Garante fallback estável para UTC-03.
    """
    fallback = datetime.timezone(datetime.timedelta(hours=-3))
    if not ZoneInfo:
        return fallback
    try:
        return ZoneInfo("America/Sao_Paulo")
    except (ZoneInfoNotFoundError, OSError, KeyError):
        return fallback


FUSO_BRASIL = obter_fuso_brasil()
UTC = datetime.timezone.utc
PRINT_LOCK = threading.Lock()
CLIENT_CACHE = threading.local()
LOG_CALLBACK: Optional[Callable[[str], None]] = None

FiltroFunc = Callable[[str], bool]


def set_log_callback(callback: Optional[Callable[[str], None]]):
    """Define função customizada para receber os logs deste módulo."""
    global LOG_CALLBACK
    LOG_CALLBACK = callback


@contextmanager
def temporary_log_callback(callback: Optional[Callable[[str], None]]):
    """Context manager para sobrescrever temporariamente o callback de log."""
    previous = LOG_CALLBACK
    set_log_callback(callback)
    try:
        yield
    finally:
        set_log_callback(previous)


def log(msg: str):
    if LOG_CALLBACK:
        LOG_CALLBACK(msg)
        return
    with PRINT_LOCK:
        print(msg, flush=True)


def para_fuso_brasil(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(FUSO_BRASIL)


def formatar_brasil(dt):
    ajustado = para_fuso_brasil(dt)
    return ajustado.isoformat(timespec="seconds") if ajustado else ""


def dividir_periodo(
    data_inicio: datetime.date, data_fim: datetime.date, max_blocos: int
) -> List[Tuple[datetime.date, datetime.date]]:
    dias_totais = (data_fim - data_inicio).days + 1
    blocos = max(1, min(max_blocos, dias_totais))
    tamanho_bloco = max(1, (dias_totais + blocos - 1) // blocos)

    intervalos = []
    inicio = data_inicio
    while inicio <= data_fim:
        fim = min(inicio + datetime.timedelta(days=tamanho_bloco - 1), data_fim)
        intervalos.append((inicio, fim))
        inicio = fim + datetime.timedelta(days=1)
    return intervalos


def get_twilio_client(acc_sid: str, auth_tok: str) -> Client:
    """
    Retorna um cliente Twilio reutilizando uma instância por thread.
    Evita refazer o handshake HTTP para cada bloco.
    """
    cached = getattr(CLIENT_CACHE, "client", None)
    if cached and cached["sid"] == acc_sid and cached["token"] == auth_tok:
        return cached["client"]

    client = Client(acc_sid, auth_tok)
    CLIENT_CACHE.client = {"sid": acc_sid, "token": auth_tok, "client": client}
    return client


def preparar_filtro(filtro: str, usar_regex: bool) -> Optional[FiltroFunc]:
    """
    Prepara uma função de filtro reaproveitável para acelerar o processamento.
    Retorna None quando nenhum filtro deve ser aplicado.
    """
    if not filtro:
        return None

    if usar_regex:
        padrao = re.compile(filtro, re.IGNORECASE)

        def _aplicar_regex(texto: str) -> bool:
            return bool(padrao.search(texto))

        return _aplicar_regex

    filtro_lower = filtro.lower()

    def _aplicar_contem(texto: str) -> bool:
        return filtro_lower in texto.lower()

    return _aplicar_contem


def processar_bloco(
    indice_bloco: int,
    data_inicio: datetime.date,
    data_fim: datetime.date,
    filtro_func: Optional[FiltroFunc],
    acc_sid: str,
    auth_tok: str,
 ) -> Dict[str, object]:
    inicio_brt = datetime.datetime.combine(data_inicio, datetime.time.min, tzinfo=FUSO_BRASIL)
    fim_brt = datetime.datetime.combine(data_fim + datetime.timedelta(days=1), datetime.time.min, tzinfo=FUSO_BRASIL)
    inicio_utc = inicio_brt.astimezone(UTC)
    fim_utc = fim_brt.astimezone(UTC)

    cliente = get_twilio_client(acc_sid, auth_tok)

    processadas = 0
    registros = []

    log(f"[Bloco {indice_bloco}] Iniciando busca ({data_inicio.isoformat()}→{data_fim.isoformat()})…")

    for msg in cliente.messages.stream(
        date_sent_after=inicio_utc,
        date_sent_before=fim_utc,
        page_size=1000,
    ):
        processadas += 1

        if processadas % 1000 == 0:
            log(f"[Bloco {indice_bloco}] Processadas={processadas} (parciais)")

        body_text = msg.body or ""
        if filtro_func and not filtro_func(body_text):
            continue

        data_sent = msg.date_sent
        data_created = msg.date_created
        if data_sent and data_sent.tzinfo is None:
            data_sent = data_sent.replace(tzinfo=UTC)
        if data_created and data_created.tzinfo is None:
            data_created = data_created.replace(tzinfo=UTC)

        sort_key = data_sent or data_created or datetime.datetime.min.replace(tzinfo=UTC)

        row = [
            msg.sid,
            msg.from_ or "",
            msg.to or "",
            msg.status or "",
            formatar_brasil(msg.date_created),
            formatar_brasil(msg.date_sent),
            getattr(msg, "error_code", "") or "",
            getattr(msg, "error_message", "") or "",
            getattr(msg, "num_segments", "") or "",
            msg.price or "",
            msg.direction or "",
            body_text,
        ]

        registros.append(
            {
                "sid": msg.sid,
                "to": msg.to or "",
                "date_sent": data_sent,
                "date_created": data_created,
                "sort_key": sort_key,
                "row": row,
            }
        )

    log(
        f"[Bloco {indice_bloco}] Finalizado | processadas={processadas} | encontradas={len(registros)} "
        f"| intervalo={data_inicio.isoformat()}→{data_fim.isoformat()}"
    )

    return {
        "indice": indice_bloco,
        "processadas": processadas,
        "encontradas": len(registros),
        "registros": registros,
    }


def _coerce_date(value: Union[str, datetime.date, datetime.datetime]) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if not isinstance(value, str):
        raise TypeError("Datas devem ser string (YYYY-MM-DD) ou objetos date/datetime.")
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Data inválida. Use formato YYYY-MM-DD (ex: 2025-09-07)") from exc


def gerar_relatorio_twilio(
    data_inicio: Union[str, datetime.date, datetime.datetime],
    data_fim: Union[str, datetime.date, datetime.datetime],
    *,
    filtro: str = "",
    usar_regex: bool = False,
    arquivo_saida: str = "relatorio-hiper.xlsx",
    num_workers: int = NUM_WORKERS,
    acc_sid: Optional[str] = None,
    auth_tok: Optional[str] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, object]:
    """
    Baixa mensagens do Twilio no intervalo informado e salva em um XLSX.
    Retorna um dicionário com informações do processamento.
    """

    acc = acc_sid or os.getenv("TWILIO_ACCOUNT_SID") or DEFAULT_ACCOUNT_SID
    tok = auth_tok or os.getenv("TWILIO_AUTH_TOKEN") or DEFAULT_AUTH_TOKEN
    if not acc or not tok:
        raise ValueError("Credenciais do Twilio não configuradas.")

    data_inicio_dt = _coerce_date(data_inicio)
    data_fim_dt = _coerce_date(data_fim)
    if data_inicio_dt > data_fim_dt:
        raise ValueError("Data de início deve ser anterior à data de fim.")

    if num_workers < 1:
        raise ValueError("NUM_WORKERS deve ser pelo menos 1.")

    output_path = Path(arquivo_saida).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with temporary_log_callback(log_callback):
        log(f"🔍 Buscando mensagens do período: {data_inicio_dt} até {data_fim_dt}")
        log("📱 Conectando ao Twilio...")

        filtro_func = preparar_filtro(filtro, usar_regex)

        get_twilio_client(acc, tok)
        log("✅ Conectado ao Twilio com sucesso!")

        log(f"📋 Criando planilha: {output_path.name}")
        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title="Mensagens_Periodo")

        headers = [
            "sid",
            "from",
            "to",
            "status",
            "date_created",
            "date_sent",
            "error_code",
            "error_message",
            "num_segments",
            "price",
            "direction",
            "body",
        ]
        ws.append(headers)

        intervalos = dividir_periodo(data_inicio_dt, data_fim_dt, num_workers)
        log(f"🧵 Dividindo intervalo em {len(intervalos)} bloco(s) para requisições paralelas...")
        for idx, (inicio_bloco, fim_bloco) in enumerate(intervalos, start=1):
            log(f"   • Bloco {idx}: {inicio_bloco.isoformat()} → {fim_bloco.isoformat()}")

        if filtro_func:
            modo = "regex" if usar_regex else "texto simples"
            log(f"📝 Filtro ({modo}): {filtro}")
        else:
            log("📝 Sem filtro aplicado.")
        log("🔎 Iniciando busca por mensagens...")

        resultados = []

        max_workers = min(len(intervalos), num_workers) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tarefas = [
                executor.submit(
                    processar_bloco,
                    indice,
                    inicio_bloco,
                    fim_bloco,
                    filtro_func,
                    acc,
                    tok,
                )
                for indice, (inicio_bloco, fim_bloco) in enumerate(intervalos, start=1)
            ]

            for futuro in as_completed(tarefas):
                resultado = futuro.result()
                resultados.append(resultado)
                log(f"📦 Resultado recebido do bloco {resultado['indice']}.")

        total_processadas = sum(r["processadas"] for r in resultados)
        registros_combinados = {}
        for resultado in resultados:
            for registro in resultado["registros"]:
                registros_combinados[registro["sid"]] = registro

        mensagens_ordenadas = sorted(
            registros_combinados.values(),
            key=lambda item: (item["sort_key"], item["sid"]),
        )

        log("─" * 50)

        total = 0
        dia_atual = None
        for registro in mensagens_ordenadas:
            data_envio = registro["date_sent"]
            data_envio_brasil = para_fuso_brasil(data_envio) if data_envio else None
            dia_msg = data_envio_brasil.date() if data_envio_brasil else None

            if dia_msg and dia_msg != dia_atual:
                dia_atual = dia_msg
                log(f"📅 Processando dia: {dia_atual.strftime('%d/%m/%Y')}")

            total += 1
            log(f"✅ Encontrada #{total}: {registro['to']} - {formatar_brasil(data_envio)}")
            ws.append(registro["row"])

        log("─" * 50)
        log(f"💾 Salvando arquivo: {output_path}")
        wb.save(str(output_path))
        log(f"🎉 Pronto! {total} mensagens encontradas de {total_processadas} processadas")
        log(f"📁 Período: {data_inicio_dt} a {data_fim_dt}")
        log(f"📄 Arquivo salvo: {output_path}")

    return {
        "arquivo": output_path,
        "total_encontradas": total,
        "total_processadas": total_processadas,
        "intervalo": (data_inicio_dt, data_fim_dt),
    }


def main():
    try:
        gerar_relatorio_twilio(
            DATA_INICIO,
            DATA_FIM,
            filtro=FILTRO,
            usar_regex=USAR_REGEX,
            arquivo_saida=ARQUIVO_SAIDA,
            num_workers=NUM_WORKERS,
        )
    except Exception as exc:
        log(f"❌ Erro ao gerar relatório: {exc}")

if __name__ == "__main__":
    main()
