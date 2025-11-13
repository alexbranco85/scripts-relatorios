# RelatorioSMS

## Empacotamento no Windows

```sh
python -m venv .venv && .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
```

**Defina as credenciais do Twilio** antes de executar ou empacotar:

```sh
set TWILIO_ACCOUNT_SID=...
set TWILIO_AUTH_TOKEN=...
```
Ou edite os padrões diretamente no script.

**Gerar o executável GUI:**
```sh
pyinstaller --noconfirm --onefile --windowed --name RelatorioSMS relatorio_sms_app.py
```
O binário será criado em `dist\RelatorioSMS.exe`. Copie junto eventuais arquivos de apoio (planilhas, etc.) e teste abrindo o `.exe`.

---

## Uso da GUI

- Execute `python relatorio_sms_app.py` (ou o `.exe`) para abrir a interface.
- Preencha data inicial/final e, opcionalmente, ajuste o filtro regex para baixar o XLSX. O arquivo gerado já entra na lista de arquivos para o PDF.
- Adicione outros arquivos CSV/JSON/XLSX caso queira consolidar mais de um arquivo e informe o nome do PDF antes de clicar em **Gerar PDF**.
- Os logs mostram o andamento; mensagens de sucesso/erro também aparecem em pop‑ups.

---

## Verificação

```sh
python3 -m py_compile script_relatorio.py analisar_e_gerar_pdf.py relatorio_sms_app.py
```

---

## Próximos passos sugeridos

- Testar a GUI com credenciais reais para garantir que o download do Twilio e a geração do PDF ocorram sem bloqueios específicos do ambiente.
- Após gerar o `.exe`, executar no Windows final para conferir se o Matplotlib/Tkinter estão embutidos corretamente (fonts, gráficos e diálogos).

---


## Outros scripts:

- Crie o venv:
python3 -m venv .venv

- Ative:
source .venv/bin/activate

- Agora instale as dependências necessárias

- Rode o script desejado.
