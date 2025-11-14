#!/usr/bin/env python3
"""Aplicação Flask com os mesmos fluxos da GUI desktop."""

from __future__ import annotations

import io
import os
import secrets
import shutil
import tempfile
import threading
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional
import re

from flask import (
    Flask,
    abort,
    after_this_request,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

import analisar_e_gerar_pdf as analise
import script_relatorio

app = Flask(__name__)
app.secret_key = os.getenv("RELATORIO_SMS_WEB_SECRET", "relatorio-sms-web")

DOWNLOAD_CACHE: Dict[str, Dict[str, object]] = {}
CACHE_LOCK = threading.Lock()
PLANILHA_JOBS: Dict[str, Dict[str, object]] = {}
PLANILHA_LOCK = threading.Lock()
PDF_JOBS: Dict[str, Dict[str, object]] = {}
PDF_LOCK = threading.Lock()
PROGRESS_REGEX = re.compile(r"Encontrada #?(\d+)")
MAX_LOG_ITEMS = 200


class _StreamingLogger:
    """Captura writes e envia linha a linha para um callback."""

    def __init__(self, emitter: Callable[[str], None]):
        self._emitter = emitter
        self._buffer = ""

    def write(self, data: str):
        if not data:
            return 0
        self._buffer += data
        while "\n" in self._buffer:
            linha, self._buffer = self._buffer.split("\n", 1)
            texto = linha.strip()
            if texto:
                self._emitter(texto)
        return len(data)

    def flush(self):
        if self._buffer.strip():
            self._emitter(self._buffer.strip())
        self._buffer = ""


def _default_filename(extensao: str) -> str:
    return f"relatorio_sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensao}"


def _sanitize_filename(nome: str, extensao_padrao: str) -> str:
    nome_limpo = secure_filename(nome or "")
    if not nome_limpo:
        nome_limpo = _default_filename(extensao_padrao.lstrip("."))
    if not nome_limpo.lower().endswith(extensao_padrao):
        nome_limpo = f"{nome_limpo}{extensao_padrao}"
    return nome_limpo


def _registrar_download(arquivo: Path, download_name: str, cleanup_dir: Optional[Path]) -> str:
    token = secrets.token_urlsafe(16)
    with CACHE_LOCK:
        DOWNLOAD_CACHE[token] = {
            "path": arquivo,
            "name": download_name,
            "cleanup": cleanup_dir,
        }
    return token


def _resgatar_download(token: str) -> Optional[Dict[str, object]]:
    with CACHE_LOCK:
        return DOWNLOAD_CACHE.pop(token, None)


def _registrar_log_job(job_id: str, mensagem: str):
    match = PROGRESS_REGEX.search(mensagem)
    with PLANILHA_LOCK:
        job = PLANILHA_JOBS.get(job_id)
        if not job:
            return
        logs = job.setdefault("logs", [])
        logs.append(mensagem)
        if len(logs) > MAX_LOG_ITEMS:
            job["logs"] = logs[-MAX_LOG_ITEMS:]
        valor: Optional[int] = None
        if match:
            valor = int(match.group(1))
        elif "Encontrada" in mensagem:
            valor = job.get("encontradas", 0) + 1
        if valor is not None:
            job["encontradas"] = max(job.get("encontradas", 0), valor)


def _atualizar_job(job_id: str, **campos):
    with PLANILHA_LOCK:
        job = PLANILHA_JOBS.get(job_id)
        if not job:
            return
        job.update(campos)


def _obter_job(job_id: str) -> Optional[Dict[str, object]]:
    with PLANILHA_LOCK:
        job = PLANILHA_JOBS.get(job_id)
        if not job:
            return None
        copia = job.copy()
        if "logs" in copia:
            copia["logs"] = list(copia["logs"])
        return copia


def _iniciar_job_planilha(
    inicio: str,
    fim: str,
    filtro: str,
    usar_regex: bool,
    nome_saida: str,
):
    job_id = secrets.token_urlsafe(12)
    with PLANILHA_LOCK:
        PLANILHA_JOBS[job_id] = {
            "status": "running",
            "logs": [],
            "encontradas": 0,
            "processados": 0,
            "mensagem": "",
            "download_token": None,
            "erro": None,
        }

    thread = threading.Thread(
        target=_worker_job_planilha,
        args=(job_id, inicio, fim, filtro, usar_regex, nome_saida),
        daemon=True,
    )
    thread.start()
    return job_id


def _worker_job_planilha(
    job_id: str,
    inicio: str,
    fim: str,
    filtro: str,
    usar_regex: bool,
    nome_saida: str,
):
    temp_dir = Path(tempfile.mkdtemp(prefix="relatorio_sms_xlsx_"))
    saida = temp_dir / nome_saida

    def callback(msg: str):
        _registrar_log_job(job_id, msg)

    try:
        resultado = script_relatorio.gerar_relatorio_twilio(
            inicio,
            fim,
            filtro=filtro,
            usar_regex=usar_regex,
            arquivo_saida=str(saida),
            num_workers=script_relatorio.NUM_WORKERS,
            log_callback=callback,
        )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(temp_dir, ignore_errors=True)
        _atualizar_job(job_id, status="error", erro=str(exc))
        return

    token = _registrar_download(saida, nome_saida, temp_dir)
    mensagem = (
        f"Planilha pronta com {resultado['total_encontradas']} registro(s)"
        f" em {resultado['total_processadas']} processados."
    )

    _atualizar_job(
        job_id,
        status="done",
        mensagem=mensagem,
        download_token=token,
        encontradas=resultado.get("total_encontradas", 0),
        processados=resultado.get("total_processadas", 0),
    )


def _registrar_log_pdf(job_id: str, mensagem: str):
    with PDF_LOCK:
        job = PDF_JOBS.get(job_id)
        if not job:
            return
        logs = job.setdefault("logs", [])
        logs.append(mensagem)
        if len(logs) > MAX_LOG_ITEMS:
            job["logs"] = logs[-MAX_LOG_ITEMS:]


def _atualizar_job_pdf(job_id: str, **campos):
    with PDF_LOCK:
        job = PDF_JOBS.get(job_id)
        if not job:
            return
        job.update(campos)


def _obter_job_pdf(job_id: str) -> Optional[Dict[str, object]]:
    with PDF_LOCK:
        job = PDF_JOBS.get(job_id)
        if not job:
            return None
        copia = job.copy()
        if "logs" in copia:
            copia["logs"] = list(copia["logs"])
        return copia


def _iniciar_job_pdf(
    arquivos: List[Path],
    filtro: str,
    usar_regex: bool,
    destino_pdf: Path,
    nome_pdf: str,
    texto_sms: Optional[str],
    subtitle: Optional[str],
    temp_dir: Path,
):
    job_id = secrets.token_urlsafe(12)
    with PDF_LOCK:
        PDF_JOBS[job_id] = {
            "status": "running",
            "logs": [],
            "mensagem": "",
            "erro": None,
            "download_token": None,
        }

    thread = threading.Thread(
        target=_worker_job_pdf,
        args=(job_id, arquivos, filtro, usar_regex, destino_pdf, nome_pdf, texto_sms, subtitle, temp_dir),
        daemon=True,
    )
    thread.start()
    return job_id


def _worker_job_pdf(
    job_id: str,
    arquivos: List[Path],
    filtro: str,
    usar_regex: bool,
    destino_pdf: Path,
    nome_pdf: str,
    texto_sms: Optional[str],
    subtitle: Optional[str],
    temp_dir: Path,
):
    logger = _StreamingLogger(lambda linha: _registrar_log_pdf(job_id, linha))
    try:
        _registrar_log_pdf(job_id, "🖨️ Iniciando geração do PDF...")
        with redirect_stdout(logger):
            pdf_path = analise.gerar_pdf_relatorio(
                arquivos,
                filtro=filtro,
                usar_regex=usar_regex,
                arquivo_pdf_saida=str(destino_pdf),
                texto_sms=texto_sms,
                subtitle=subtitle,
            )
        logger.flush()
    except Exception as exc:  # noqa: BLE001
        logger.flush()
        shutil.rmtree(temp_dir, ignore_errors=True)
        _atualizar_job_pdf(job_id, status="error", erro=str(exc))
        return

    token = _registrar_download(Path(pdf_path), nome_pdf, temp_dir)
    _atualizar_job_pdf(
        job_id,
        status="done",
        mensagem="PDF gerado com sucesso.",
        download_token=token,
    )


def _validar_data(valor: str) -> str:
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Datas devem estar no formato YYYY-MM-DD.") from None
    return valor


@app.route("/")
def index():
    hoje = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "index.html",
        start_date=hoje,
        end_date=hoje,
        sms_filter=script_relatorio.FILTRO or "",
        sms_regex=script_relatorio.USAR_REGEX,
        pdf_filter=analise.FILTRO or "",
        pdf_regex=analise.USAR_REGEX,
        pdf_texto_sms=analise.TEXTO_SMS or "",
        pdf_subtitle=analise.SUBTITLE or "",
        xlsx_filename=_default_filename("xlsx"),
        pdf_filename=_default_filename("pdf"),
    )


@app.post("/gerar-planilha")
def gerar_planilha():
    inicio = request.form.get("start_date", "").strip()
    fim = request.form.get("end_date", "").strip()
    filtro = request.form.get("sms_filter", "").strip()
    usar_regex = request.form.get("sms_regex") == "on"
    nome_saida = _sanitize_filename(request.form.get("xlsx_filename", ""), ".xlsx")
    quer_json = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"

    try:
        inicio = _validar_data(inicio)
        fim = _validar_data(fim)
    except ValueError as exc:
        if quer_json:
            return jsonify({"error": str(exc)}), 400
        flash(str(exc), "error")
        return redirect(url_for("index"))

    if quer_json:
        job_id = _iniciar_job_planilha(inicio, fim, filtro, usar_regex, nome_saida)
        return jsonify({"job_id": job_id, "status": "running"}), 202

    logs: List[str] = []

    def callback(msg: str):
        logs.append(msg)

    temp_dir = Path(tempfile.mkdtemp(prefix="relatorio_sms_xlsx_"))
    saida = temp_dir / nome_saida

    try:
        resultado = script_relatorio.gerar_relatorio_twilio(
            inicio,
            fim,
            filtro=filtro,
            usar_regex=usar_regex,
            arquivo_saida=str(saida),
            num_workers=script_relatorio.NUM_WORKERS,
            log_callback=callback,
        )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(temp_dir, ignore_errors=True)
        flash(f"Erro ao gerar planilha: {exc}", "error")
        return redirect(url_for("index"))

    token = _registrar_download(saida, nome_saida, temp_dir)
    mensagem = (
        f"Planilha pronta com {resultado['total_encontradas']} registro(s)"
        f" em {resultado['total_processadas']} processados."
    )

    return render_template(
        "resultado.html",
        titulo="Planilha do Twilio",
        sucesso=True,
        mensagem=mensagem,
        log_text="\n".join(logs),
        download_token=token,
        download_rotulo="Baixar XLSX",
    )


@app.post("/gerar-pdf")
def gerar_pdf():
    arquivos = request.files.getlist("arquivos")
    filtro = request.form.get("pdf_filter", "").strip()
    usar_regex = request.form.get("pdf_regex") == "on"
    texto_sms = request.form.get("pdf_texto_sms", "").strip() or None
    subtitle = request.form.get("pdf_subtitle", "").strip() or None
    nome_pdf = _sanitize_filename(request.form.get("pdf_filename", ""), ".pdf")
    quer_json = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"

    arquivos_validos = [arquivo for arquivo in arquivos if arquivo and arquivo.filename]
    if not arquivos_validos:
        if quer_json:
            return jsonify({"error": "Selecione ao menos um arquivo para gerar o PDF."}), 400
        flash("Selecione ao menos um arquivo para gerar o PDF.", "error")
        return redirect(url_for("index"))

    temp_dir = Path(tempfile.mkdtemp(prefix="relatorio_sms_pdf_"))
    uploads: List[Path] = []
    for arquivo in arquivos_validos:
        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            continue
        destino = temp_dir / nome_seguro
        arquivo.save(destino)
        uploads.append(destino)

    if not uploads:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if quer_json:
            return jsonify({"error": "Nenhum arquivo válido recebido."}), 400
        flash("Nenhum arquivo válido recebido.", "error")
        return redirect(url_for("index"))

    destino_pdf = temp_dir / nome_pdf

    if quer_json:
        job_id = _iniciar_job_pdf(
            uploads,
            filtro,
            usar_regex,
            destino_pdf,
            nome_pdf,
            texto_sms,
            subtitle,
            temp_dir,
        )
        return jsonify({"job_id": job_id, "status": "running"}), 202

    buffer = io.StringIO()
    log_buffer: List[str] = []

    try:
        with redirect_stdout(buffer):
            pdf_path = analise.gerar_pdf_relatorio(
                uploads,
                filtro=filtro,
                usar_regex=usar_regex,
                arquivo_pdf_saida=str(destino_pdf),
                texto_sms=texto_sms,
                subtitle=subtitle,
            )
    except Exception as exc:  # noqa: BLE001
        log_buffer.extend(buffer.getvalue().splitlines())
        shutil.rmtree(temp_dir, ignore_errors=True)
        flash(f"Erro ao gerar PDF: {exc}", "error")
        return redirect(url_for("index"))

    log_buffer.extend(buffer.getvalue().splitlines())

    token = _registrar_download(Path(pdf_path), nome_pdf, temp_dir)

    return render_template(
        "resultado.html",
        titulo="PDF consolidado",
        sucesso=True,
        mensagem="PDF gerado com sucesso.",
        log_text="\n".join(log_buffer),
        download_token=token,
        download_rotulo="Baixar PDF",
    )


@app.get("/api/planilha/<job_id>")
def status_planilha(job_id: str):
    job = _obter_job(job_id)
    if not job:
        abort(404)

    token = job.get("download_token")
    data = {
        "status": job.get("status"),
        "mensagem": job.get("mensagem"),
        "erro": job.get("erro"),
        "encontradas": job.get("encontradas", 0),
        "processados": job.get("processados", 0),
        "logs": job.get("logs", []),
    }
    if token:
        data["download_token"] = token
        data["download_url"] = url_for("baixar_arquivo", token=token)

    return jsonify(data)


@app.get("/api/pdf/<job_id>")
def status_pdf(job_id: str):
    job = _obter_job_pdf(job_id)
    if not job:
        abort(404)

    data = {
        "status": job.get("status"),
        "mensagem": job.get("mensagem"),
        "erro": job.get("erro"),
        "logs": job.get("logs", []),
    }
    token = job.get("download_token")
    if token:
        data["download_token"] = token
        data["download_url"] = url_for("baixar_arquivo", token=token)

    return jsonify(data)


@app.get("/download/<token>")
def baixar_arquivo(token: str):
    registro = _resgatar_download(token)
    if not registro:
        abort(404)

    caminho = registro["path"]
    nome = registro["name"]
    cleanup_dir = registro.get("cleanup")

    if not isinstance(caminho, Path) or not caminho.exists():
        abort(410)

    @after_this_request
    def _cleanup(response):  # type: ignore[override]
        try:
            if caminho.exists():
                caminho.unlink()
        except OSError:
            pass
        if isinstance(cleanup_dir, Path):
            shutil.rmtree(cleanup_dir, ignore_errors=True)
        return response

    return send_file(caminho, as_attachment=True, download_name=nome)


if __name__ == "__main__":
    app.run(debug=True)
