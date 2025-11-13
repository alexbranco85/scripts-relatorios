#!/usr/bin/env python3
"""
Interface unificada para baixar os SMS do Twilio em XLSX e gerar o PDF consolidado.

Este script reutiliza a lógica existente em script_relatorio.py e analisar_e_gerar_pdf.py,
expondo um fluxo simples para usuários finais (ideal para empacotar em .exe).
"""

from __future__ import annotations

import io
import queue
import threading
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import analisar_e_gerar_pdf as analise
import script_relatorio


class RelatorioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Relatório SMS - ApostaTudo")
        self.geometry("960x720")
        self.minsize(820, 640)

        self.log_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.selected_files: List[str] = []
        self._last_generated_file: Optional[Path] = None

        self._build_variables()
        self._build_ui()

        self.after(200, self._process_log_queue)

    def _build_variables(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.start_date_var = tk.StringVar(value=hoje)
        self.end_date_var = tk.StringVar(value=hoje)
        self.sms_filter_var = tk.StringVar(value=script_relatorio.FILTRO)
        self.sms_regex_var = tk.BooleanVar(value=script_relatorio.USAR_REGEX)
        self.xlsx_saida_var = tk.StringVar(value=self._default_nome_saida("xlsx"))

        self.pdf_filter_var = tk.StringVar(value=analise.FILTRO)
        self.pdf_regex_var = tk.BooleanVar(value=analise.USAR_REGEX)
        self.pdf_saida_var = tk.StringVar(value=self._default_nome_saida("pdf"))

        self.arquivos_label_var = tk.StringVar()
        self._atualizar_lista_arquivos()

    def _default_nome_saida(self, extensao: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"relatorio_sms_{timestamp}.{extensao}"

    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_coleta_frame(main)
        self._build_pdf_frame(main)
        self._build_log_frame(main)

    def _build_coleta_frame(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="1. Baixar dados do Twilio (gera XLSX)")
        frame.pack(fill="x", pady=(0, 12))

        ttk.Label(frame, text="Data início (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.start_date_var, width=16).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frame, text="Data fim (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.end_date_var, width=16).grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(frame, text="Filtro de texto / regex").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.sms_filter_var, width=50).grid(row=1, column=1, columnspan=2, sticky="we", padx=6, pady=4)
        ttk.Checkbutton(frame, text="Usar regex", variable=self.sms_regex_var).grid(row=1, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(frame, text="Arquivo XLSX de saída").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.xlsx_saida_var).grid(row=2, column=1, columnspan=2, sticky="we", padx=6, pady=4)
        ttk.Button(frame, text="Selecionar…", command=self._selecionar_saida_xlsx).grid(row=2, column=3, sticky="we", padx=6, pady=4)

        self.btn_planilha = ttk.Button(frame, text="Gerar planilha a partir do Twilio", command=self._iniciar_geracao_planilha)
        self.btn_planilha.grid(row=3, column=0, columnspan=4, sticky="we", padx=6, pady=(8, 4))

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _build_pdf_frame(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="2. Gerar PDF do relatório")
        frame.pack(fill="x", pady=(0, 12))

        botoes_frame = ttk.Frame(frame)
        botoes_frame.grid(row=0, column=0, columnspan=4, sticky="we", padx=6, pady=4)

        self.btn_add_files = ttk.Button(botoes_frame, text="Selecionar arquivos…", command=self._selecionar_arquivos)
        self.btn_add_files.pack(side="left", padx=(0, 6))

        self.btn_use_last = ttk.Button(
            botoes_frame,
            text="Usar última planilha gerada",
            command=self._usar_ultimo_arquivo,
        )
        self.btn_use_last.pack(side="left", padx=(0, 6))

        self.btn_clear_files = ttk.Button(botoes_frame, text="Limpar seleção", command=self._limpar_arquivos)
        self.btn_clear_files.pack(side="left")

        ttk.Label(frame, textvariable=self.arquivos_label_var, justify="left").grid(
            row=1, column=0, columnspan=4, sticky="we", padx=6, pady=4
        )

        ttk.Label(frame, text="Filtro (PDF)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.pdf_filter_var, width=50).grid(row=2, column=1, columnspan=2, sticky="we", padx=6, pady=4)
        ttk.Checkbutton(frame, text="Usar regex", variable=self.pdf_regex_var).grid(row=2, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(frame, text="Arquivo PDF de saída").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.pdf_saida_var).grid(row=3, column=1, columnspan=2, sticky="we", padx=6, pady=4)
        ttk.Button(frame, text="Selecionar…", command=self._selecionar_saida_pdf).grid(row=3, column=3, sticky="we", padx=6, pady=4)

        self.btn_pdf = ttk.Button(frame, text="Gerar PDF consolidado", command=self._iniciar_geracao_pdf)
        self.btn_pdf.grid(row=4, column=0, columnspan=4, sticky="we", padx=6, pady=(8, 4))

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _build_log_frame(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="Log")
        frame.pack(fill="both", expand=True)

        self.log_text = ScrolledText(frame, height=18, state="disabled", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        self.log_text.tag_configure("info", foreground="#212529")
        self.log_text.tag_configure("success", foreground="#0f5132")
        self.log_text.tag_configure("error", foreground="#842029")

    # =============================================================================
    # Helpers de UI
    # =============================================================================
    def _selecionar_saida_xlsx(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar planilha",
            defaultextension=".xlsx",
            filetypes=[("Planilhas Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
            initialfile=self.xlsx_saida_var.get(),
        )
        if caminho:
            self.xlsx_saida_var.set(caminho)

    def _selecionar_saida_pdf(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar PDF",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
            initialfile=self.pdf_saida_var.get(),
        )
        if caminho:
            self.pdf_saida_var.set(caminho)

    def _selecionar_arquivos(self):
        arquivos = filedialog.askopenfilenames(
            title="Selecionar arquivos para o PDF",
            filetypes=[
                ("Planilhas/CSV/JSON", "*.xlsx *.xlsm *.csv *.json *.jsonl"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if arquivos:
            for arquivo in arquivos:
                if arquivo not in self.selected_files:
                    self.selected_files.append(arquivo)
            self._atualizar_lista_arquivos()

    def _limpar_arquivos(self):
        self.selected_files.clear()
        self._atualizar_lista_arquivos()

    def _usar_ultimo_arquivo(self):
        if self._last_generated_file and self._last_generated_file.exists():
            caminho = str(self._last_generated_file)
            if caminho not in self.selected_files:
                self.selected_files.append(caminho)
                self._atualizar_lista_arquivos()
            else:
                messagebox.showinfo("Relatório", "A última planilha gerada já está na lista.")
        else:
            messagebox.showwarning("Relatório", "Ainda não existe uma planilha gerada nesta sessão.")

    def _atualizar_lista_arquivos(self):
        if self.selected_files:
            lines = [f"• {Path(arquivo).name} ({arquivo})" for arquivo in self.selected_files]
        else:
            lines = ["Nenhum arquivo selecionado."]
        self.arquivos_label_var.set("\n".join(lines))

    def _set_acoes_habilitadas(self, habilitado: bool):
        estado = "normal" if habilitado else "disabled"
        for botao in (self.btn_planilha, self.btn_pdf, self.btn_add_files, self.btn_clear_files, self.btn_use_last):
            botao.configure(state=estado)

    def _log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((level, f"[{timestamp}] {message}"))

    def _log_callback(self, message: str):
        """Callback simples para ligar com script_relatorio."""
        self._log(message)

    def _process_log_queue(self):
        try:
            while True:
                level, line = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n", level)
                self.log_text.configure(state="disabled")
                self.log_text.see("end")
        except queue.Empty:
            pass
        finally:
            self.after(200, self._process_log_queue)

    def _validar_datas(self, inicio: str, fim: str) -> bool:
        try:
            datetime.strptime(inicio, "%Y-%m-%d")
            datetime.strptime(fim, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Datas inválidas", "Use o formato YYYY-MM-DD para as datas.")
            return False
        return True

    def _resolver_caminho(self, caminho: str) -> Path:
        path = Path(caminho).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _executar_em_thread(self, alvo, *args):
        thread = threading.Thread(target=alvo, args=args, daemon=True)
        thread.start()

    # =============================================================================
    # Fluxo: gerar planilha
    # =============================================================================
    def _iniciar_geracao_planilha(self):
        inicio = self.start_date_var.get().strip()
        fim = self.end_date_var.get().strip()
        if not self._validar_datas(inicio, fim):
            return

        saida = self.xlsx_saida_var.get().strip() or self._default_nome_saida("xlsx")
        self.xlsx_saida_var.set(saida)
        saida_path = self._resolver_caminho(saida)

        filtro = self.sms_filter_var.get().strip()
        usar_regex = self.sms_regex_var.get()

        self._set_acoes_habilitadas(False)
        self._log("🚀 Iniciando coleta no Twilio…")
        self._executar_em_thread(
            self._worker_planilha,
            inicio,
            fim,
            filtro,
            usar_regex,
            saida_path,
        )

    def _worker_planilha(self, inicio: str, fim: str, filtro: str, usar_regex: bool, saida: Path):
        try:
            resultado = script_relatorio.gerar_relatorio_twilio(
                inicio,
                fim,
                filtro=filtro,
                usar_regex=usar_regex,
                arquivo_saida=str(saida),
                num_workers=script_relatorio.NUM_WORKERS,
                log_callback=self._log_callback,
            )
            self._last_generated_file = resultado["arquivo"]
            self._log(
                f"✅ Planilha pronta: {resultado['arquivo']} | {resultado['total_encontradas']} registros.",
                level="success",
            )
            self.selected_files = [str(resultado["arquivo"])]
            self.after(0, self._atualizar_lista_arquivos)
        except Exception as exc:
            self._log(f"❌ Erro ao gerar planilha: {exc}", level="error")
            self.after(0, lambda: messagebox.showerror("Erro", str(exc)))
        finally:
            self.after(0, lambda: self._set_acoes_habilitadas(True))

    # =============================================================================
    # Fluxo: gerar PDF
    # =============================================================================
    def _iniciar_geracao_pdf(self):
        if not self.selected_files:
            messagebox.showwarning("PDF", "Selecione ao menos um arquivo para gerar o PDF.")
            return

        saida = self.pdf_saida_var.get().strip() or self._default_nome_saida("pdf")
        self.pdf_saida_var.set(saida)
        saida_path = self._resolver_caminho(saida)

        filtro = self.pdf_filter_var.get().strip()
        usar_regex = self.pdf_regex_var.get()

        self._set_acoes_habilitadas(False)
        self._log("🖨️ Iniciando geração do PDF…")
        self._executar_em_thread(
            self._worker_pdf,
            list(self.selected_files),
            filtro,
            usar_regex,
            saida_path,
        )

    def _worker_pdf(self, arquivos: List[str], filtro: str, usar_regex: bool, saida: Path):
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                pdf_path = analise.gerar_pdf_relatorio(
                    arquivos,
                    filtro=filtro,
                    usar_regex=usar_regex,
                    arquivo_pdf_saida=str(saida),
                    texto_sms=filtro or None,
                )
            self._propagar_buffer(buffer)
            self._log(f"✅ PDF gerado: {pdf_path}", level="success")
            self.after(0, lambda: messagebox.showinfo("Relatório", f"PDF gerado em:\n{pdf_path}"))
        except Exception as exc:
            self._propagar_buffer(buffer)
            self._log(f"❌ Erro ao gerar PDF: {exc}", level="error")
            self.after(0, lambda: messagebox.showerror("Erro", str(exc)))
        finally:
            self.after(0, lambda: self._set_acoes_habilitadas(True))

    def _propagar_buffer(self, buffer: io.StringIO):
        conteudo = buffer.getvalue().strip()
        if conteudo:
            for linha in conteudo.splitlines():
                self._log(linha)


def main():
    app = RelatorioApp()
    app.mainloop()


if __name__ == "__main__":
    main()
