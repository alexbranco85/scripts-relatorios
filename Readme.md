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

Se você for abrir o `.exe` com duplo clique (sem um terminal), crie um arquivo `.env`
no mesmo diretório contendo:

```
TWILIO_ACCOUNT_SID=seu_sid
TWILIO_AUTH_TOKEN=seu_token
```

O script detecta automaticamente esse arquivo (ou `twilio.env`) e carrega as credenciais.
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

## Painel web (Flask)

Também há uma versão web com os mesmos fluxos do executável. Para iniciar:

1. Configure as credenciais em variáveis de ambiente (`TWILIO_ACCOUNT_SID` e `TWILIO_AUTH_TOKEN`) ou mantenha um `.env` ao lado do script, exatamente como na GUI.
2. Instale as dependências (`python -m pip install -r requirements.txt`).
3. Execute `flask --app relatorio_sms_web run --reload` (ou `python relatorio_sms_web.py` para o servidor simples de desenvolvimento).
4. Abra `http://127.0.0.1:5000` no navegador.

Funcionalidades:

- Formulário para baixar o XLSX diretamente do Twilio, com datas, filtro e escolha do nome do arquivo.
- Formulário para gerar o PDF consolidado enviando planilhas/CSV/JSON (múltiplos uploads em uma única submissão).
- Os arquivos processados ficam em diretórios temporários e são limpos assim que o download é acionado.
- Os logs aparecem na própria página de resultado junto do botão para baixar o arquivo.

Para ambientes multiusuário considere definir uma chave própria (`RELATORIO_SMS_WEB_SECRET`) e servir o Flask por trás de um servidor real (Gunicorn, nginx, etc.).

---

## Verificação

```sh
python3 -m py_compile script_relatorio.py analisar_e_gerar_pdf.py relatorio_sms_app.py relatorio_sms_web.py
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
