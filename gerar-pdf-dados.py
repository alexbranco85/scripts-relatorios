#!/usr/bin/env python3
"""
Gera um PDF de relatorio a partir dos dados consolidados por agrupamento.

- Cada agrupamento ocupa uma pagina do PDF.
- Tambem permite exportar HTML simples para inspecao ou uso em outras ferramentas.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPORT_DATA: Dict[str, object] = {
    "titulo": "Relatorio consolidado - outubro",
    "mensagens": {
        "total": 2_351_902,
        "entregues": 1_658_990,
        "nao_entregues": 692_912,
        "agrupamentos": 18,
    },
    "datas": [
        {"data": "2025-10-15", "total": 444},
        {"data": "2025-10-20", "total": 49_962},
        {"data": "2025-10-21", "total": 58_066},
        {"data": "2025-10-23", "total": 22_172},
        {"data": "2025-10-24", "total": 46_927},
        {"data": "2025-10-25", "total": 79_999},
        {"data": "2025-10-27", "total": 493_211},
        {"data": "2025-10-28", "total": 795_210},
        {"data": "2025-10-29", "total": 410_669},
        {"data": "2025-10-30", "total": 163_216},
        {"data": "2025-10-31", "total": 232_026},
    ],
    "agrupamentos": [
        {
            "id": 1,
            "total": 425_442,
            "entregues": 106_555,
            "nao_entregues": 318_887,
            "texto_base": "[ {variavel} CASHBACK Diario {variavel}",
            "exemplos": [
                "[ APOSTATUDO.BET.BR ] Sistema de CASHBACK Diario ate 20% confira agora: http://sms.apostatudo.bet.br/SVeQs1",
                "[ APOSTATUDO.BET.BR ] Sistema de CASHBACK Diario ate 20% confira agora: http://sms.apostatudo.bet.br/l2nvs1",
                "[ APOSTATUDO.BET.BR ] Sistema de CASHBACK Diario ate 20% confira agora: http://sms.apostatudo.bet.br/x2nvs1",
            ],
            "datas": [
                {"data": "2025-10-27", "total": 414_507, "entregues": 97_771, "nao_entregues": 316_736},
                {"data": "2025-10-28", "total": 1_794, "entregues": 987, "nao_entregues": 807},
                {"data": "2025-10-29", "total": 1_954, "entregues": 1_649, "nao_entregues": 305},
                {"data": "2025-10-31", "total": 7_187, "entregues": 6_148, "nao_entregues": 1_039},
            ],
        },
        {
            "id": 2,
            "total": 373_202,
            "entregues": 316_060,
            "nao_entregues": 57_142,
            "texto_base": (
                "[ APOSTATUDO BET BR ] R$30,00 Por indicacao realizada, quer saber mais? "
                "clica no link abaixo:\n{variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO BET BR ] R$30,00 Por indicacao realizada, quer saber mais? clica no link abaixo: http://sms.apostatudo.bet.br/mnEHs1",
                "[ APOSTATUDO BET BR ] R$30,00 Por indicacao realizada, quer saber mais? clica no link abaixo: http://sms.apostatudo.bet.br/3nEHs1",
                "[ APOSTATUDO BET BR ] R$30,00 Por indicacao realizada, quer saber mais? clica no link abaixo: http://sms.apostatudo.bet.br/kLqHs1",
            ],
            "datas": [
                {"data": "2025-10-28", "total": 373_202, "entregues": 316_060, "nao_entregues": 57_142},
            ],
        },
        {
            "id": 3,
            "total": 371_058,
            "entregues": 309_965,
            "nao_entregues": 61_093,
            "texto_base": (
                "[ APOSTATUDO ] URGENTE!!! A votacao do Premio RECLAME AQUI esta terminando! "
                "Confirme seu voto na\nApostaTudo! Vote: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] URGENTE!!! A votacao do Premio RECLAME AQUI esta terminando! Confirme seu voto na ApostaTudo! Vote: http://sms.apostatudo.bet.br/ZGl7d1",
                "[ APOSTATUDO ] URGENTE!!! A votacao do Premio RECLAME AQUI esta terminando! Confirme seu voto na ApostaTudo! Vote: http://sms.apostatudo.bet.br/fn56d1",
                "[ APOSTATUDO ] URGENTE!!! A votacao do Premio RECLAME AQUI esta terminando! Confirme seu voto na ApostaTudo! Vote: http://sms.apostatudo.bet.br/nn56d1",
            ],
            "datas": [
                {"data": "2025-10-29", "total": 371_058, "entregues": 309_965, "nao_entregues": 61_093},
            ],
        },
        {
            "id": 4,
            "total": 358_931,
            "entregues": 292_591,
            "nao_entregues": 66_340,
            "texto_base": (
                "[ APOSTATUDO ] So falta o seu voto! Ajude a ApostaTudo a vencer o Premio Reclame "
                "AQUI 2025! Vote agora: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] So falta o seu voto! Ajude a ApostaTudo a vencer o Premio Reclame AQUI 2025! Vote agora: http://sms.apostatudo.bet.br/guXSs1",
                "[ APOSTATUDO ] So falta o seu voto! Ajude a ApostaTudo a vencer o Premio Reclame AQUI 2025! Vote agora: http://sms.apostatudo.bet.br/YtXSs1",
                "[ APOSTATUDO ] So falta o seu voto! Ajude a ApostaTudo a vencer o Premio Reclame AQUI 2025! Vote agora: http://sms.apostatudo.bet.br/O0BSs1",
            ],
            "datas": [
                {"data": "2025-10-28", "total": 358_931, "entregues": 292_591, "nao_entregues": 66_340},
            ],
        },
        {
            "id": 5,
            "total": 222_729,
            "entregues": 180_161,
            "nao_entregues": 42_568,
            "texto_base": (
                "[ APOSTATUDO ] O HALLOWEEN TA ON!!! Missoes com ate 500 + Roleta PREMIADA + Ofertas "
                "EXCLUSIVAS para voce! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] O HALLOWEEN TA ON!!! Missoes com ate 500 + Roleta PREMIADA + Ofertas EXCLUSIVAS para voce! Link: https://sms.apostatudo.bet.br/ojtzd1",
                "[ APOSTATUDO ] O HALLOWEEN TA ON!!! Missoes com ate 500 + Roleta PREMIADA + Ofertas EXCLUSIVAS para voce! Link: https://sms.apostatudo.bet.br/sjtzd1",
                "[ APOSTATUDO ] O HALLOWEEN TA ON!!! Missoes com ate 500 + Roleta PREMIADA + Ofertas EXCLUSIVAS para voce! Link: https://sms.apostatudo.bet.br/bjtzd1",
            ],
            "datas": [
                {"data": "2025-10-31", "total": 222_729, "entregues": 180_161, "nao_entregues": 42_568},
            ],
        },
        {
            "id": 6,
            "total": 135_684,
            "entregues": 111_635,
            "nao_entregues": 24_049,
            "texto_base": (
                "[ APOSTATUDO ] SUPER HALLOWEEN! Participe das missoes especiais, concorra a super "
                "premios e garanta giros extras! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] SUPER HALLOWEEN! Participe das missoes especiais, concorra a super premios e garanta giros extras! Link: http://sms.apostatudo.bet.br/M6W9d1",
                "[ APOSTATUDO ] SUPER HALLOWEEN! Participe das missoes especiais, concorra a super premios e garanta giros extras! Link: http://sms.apostatudo.bet.br/p7W9d1",
                "[ APOSTATUDO ] SUPER HALLOWEEN! Participe das missoes especiais, concorra a super premios e garanta giros extras! Link: http://sms.apostatudo.bet.br/97W9d1",
            ],
            "datas": [
                {"data": "2025-10-30", "total": 135_684, "entregues": 111_635, "nao_entregues": 24_049},
            ],
        },
        {
            "id": 7,
            "total": 108_472,
            "entregues": 93_142,
            "nao_entregues": 15_330,
            "texto_base": "[ APOSTATUDO ] MISSOES do dia liberadas! {variavel}",
            "exemplos": [
                "[ APOSTATUDO ] MISSOES do dia liberadas! Novas Missoes com ate 200 giros para voce jogar e se divertir! Link: http://sms.apostatudo.bet.br/pQETp1",
                "[ APOSTATUDO ] MISSOES do dia liberadas! Novas Missoes com ate 200 giros para voce jogar e se divertir! Link: https://sms.apostatudo.bet.br/dfdpsw",
                "[ APOSTATUDO ] MISSOES do dia liberadas! Novas Missoes com ate 200 giros para voce jogar e se divertir! Link: http://sms.apostatudo.bet.br/7EvTp1",
            ],
            "datas": [
                {"data": "2025-10-15", "total": 444, "entregues": 383, "nao_entregues": 61},
                {"data": "2025-10-20", "total": 49_962, "entregues": 43_496, "nao_entregues": 6_466},
                {"data": "2025-10-21", "total": 58_066, "entregues": 49_263, "nao_entregues": 8_803},
            ],
        },
        {
            "id": 8,
            "total": 79_999,
            "entregues": 64_676,
            "nao_entregues": 15_323,
            "texto_base": (
                "[ APOSTATUDO ] CONTAGEM REGRESSIVA! Falta pouco pra acabar, vote na ApostaTudo e "
                "garanta nossa vitoria! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] CONTAGEM REGRESSIVA! Falta pouco pra acabar, vote na ApostaTudo e garanta nossa vitoria! Link: https://apostatudobet.com/votar",
                "[ APOSTATUDO ] CONTAGEM REGRESSIVA! Falta pouco pra acabar, vote na ApostaTudo e garanta nossa vitoria! Link: http://sms.apostatudo.bet.br/L3vNa1",
                "[ APOSTATUDO ] CONTAGEM REGRESSIVA! Falta pouco pra acabar, vote na ApostaTudo e garanta nossa vitoria! Link: http://sms.apostatudo.bet.br/yqqNa1",
            ],
            "datas": [
                {"data": "2025-10-25", "total": 79_999, "entregues": 64_676, "nao_entregues": 15_323},
            ],
        },
        {
            "id": 9,
            "total": 77_098,
            "entregues": 64_587,
            "nao_entregues": 12_511,
            "texto_base": (
                "[ APOSTATUDO ] Semana SOBRENATURAL!!! Roleta Diaria + Missoes + Oferta do dia com "
                "ate 300 giros na APOSTATUDO! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] Semana SOBRENATURAL!!! Roleta Diaria + Missoes + Oferta do dia com ate 300 giros na APOSTATUDO! Link: http://sms.apostatudo.bet.br/0NHas1",
                "[ APOSTATUDO ] Semana SOBRENATURAL!!! Roleta Diaria + Missoes + Oferta do dia com ate 300 giros na APOSTATUDO! Link: http://sms.apostatudo.bet.br/1MHas1",
                "[ APOSTATUDO ] Semana SOBRENATURAL!!! Roleta Diaria + Missoes + Oferta do dia com ate 300 giros na APOSTATUDO! Link: http://sms.apostatudo.bet.br/TMHas1",
            ],
            "datas": [
                {"data": "2025-10-27", "total": 77_098, "entregues": 64_587, "nao_entregues": 12_511},
            ],
        },
        {
            "id": 10,
            "total": 59_343,
            "entregues": 49_927,
            "nao_entregues": 9_416,
            "texto_base": (
                "[ APOSTATUDO ] HALLOWEEN PREMIADO!!! Roleta + Missoes com 500 giros + Beneficios "
                "exclusivos para voce so hoje! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] HALLOWEEN PREMIADO!!! Roleta + Missoes com 500 giros + Beneficios exclusivos para voce so hoje! Link: http://sms.apostatudo.bet.br/hTdEs1",
                "[ APOSTATUDO ] HALLOWEEN PREMIADO!!! Roleta + Missoes com 500 giros + Beneficios exclusivos para voce so hoje! Link: http://sms.apostatudo.bet.br/ITdEs1",
                "[ APOSTATUDO ] HALLOWEEN PREMIADO!!! Roleta + Missoes com 500 giros + Beneficios exclusivos para voce so hoje! Link: http://sms.apostatudo.bet.br/wOdEs1",
            ],
            "datas": [
                {"data": "2025-10-28", "total": 59_343, "entregues": 49_927, "nao_entregues": 9_416},
            ],
        },
        {
            "id": 11,
            "total": 46_912,
            "entregues": 26,
            "nao_entregues": 46_886,
            "texto_base": (
                "[ APOSTATUDO ] RETA FINAL! Seu voto pode decidir o Premio Reclame AQUI 2025. "
                "Vote {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] RETA FINAL! Seu voto pode decidir o Premio Reclame AQUI 2025. Vote agora na Aposta Tudo: https://apostatudobet.com/votar",
                "[ APOSTATUDO ] RETA FINAL! Seu voto pode decidir o Premio Reclame AQUI 2025. Vote agora na Aposta Tudo: https://apostatudobet.com/votar",
                "[ APOSTATUDO ] RETA FINAL! Seu voto pode decidir o Premio Reclame AQUI 2025. Vote agora na Aposta Tudo:",
            ],
            "datas": [
                {"data": "2025-10-24", "total": 46_912, "entregues": 26, "nao_entregues": 46_886},
            ],
        },
        {
            "id": 12,
            "total": 35_615,
            "entregues": 30_224,
            "nao_entregues": 5_391,
            "texto_base": (
                "[ APOSTATUDO ] SUPER HALLOWEEN! 500 giros em missoes tematicas! Participe e "
                "aproveite os beneficios exclusivos! Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] SUPER HALLOWEEN! 500 giros em missoes tematicas! Participe e aproveite os beneficios exclusivos! Link: http://sms.apostatudo.bet.br/2UgLs1",
                "[ APOSTATUDO ] SUPER HALLOWEEN! 500 giros em missoes tematicas! Participe e aproveite os beneficios exclusivos! Link: http://sms.apostatudo.bet.br/yUgLs1",
                "[ APOSTATUDO ] SUPER HALLOWEEN! 500 giros em missoes tematicas! Participe e aproveite os beneficios exclusivos! Link: http://sms.apostatudo.bet.br/FWgLs1",
            ],
            "datas": [
                {"data": "2025-10-29", "total": 35_615, "entregues": 30_224, "nao_entregues": 5_391},
            ],
        },
        {
            "id": 13,
            "total": 27_530,
            "entregues": 23_405,
            "nao_entregues": 4_125,
            "texto_base": (
                "[ APOSTATUDO ] VOCE FOI ESCOLHIDO!!! LUCRE MUITO com o proximo finalista da "
                "LIBERTADORES! Palmeiras x LDU Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] VOCE FOI ESCOLHIDO!!! LUCRE MUITO com o proximo finalista da LIBERTADORES! Palmeiras x LDU Link: https://sms.apostatudo.bet.br/NAokd1",
                "[ APOSTATUDO ] VOCE FOI ESCOLHIDO!!! LUCRE MUITO com o proximo finalista da LIBERTADORES! Palmeiras x LDU Link: https://sms.apostatudo.bet.br/UFokd1",
                "[ APOSTATUDO ] VOCE FOI ESCOLHIDO!!! LUCRE MUITO com o proximo finalista da LIBERTADORES! Palmeiras x LDU Link: https://sms.apostatudo.bet.br/OYakd1",
            ],
            "datas": [
                {"data": "2025-10-30", "total": 27_530, "entregues": 23_405, "nao_entregues": 4_125},
            ],
        },
        {
            "id": 14,
            "total": 22_162,
            "entregues": 12_269,
            "nao_entregues": 9_893,
            "texto_base": (
                "[ APOSTATUDO ] O seu VOTO vale Tudo! Conquistamos a indicacao ao Premio Reclame "
                "AQUI 2025! So falta o seu voto. Vote: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] O seu VOTO vale Tudo! Conquistamos a indicacao ao Premio Reclame AQUI 2025! So falta o seu voto. Vote: https://apostatudobet.com/votar",
                "[ APOSTATUDO ] O seu VOTO vale Tudo! Conquistamos a indicacao ao Premio Reclame AQUI 2025! So falta o seu voto. Vote: http://www.uol.com.br",
            ],
            "datas": [
                {"data": "2025-10-23", "total": 22_162, "entregues": 12_269, "nao_entregues": 9_893},
            ],
        },
        {
            "id": 15,
            "total": 7_687,
            "entregues": 3_744,
            "nao_entregues": 3_943,
            "texto_base": (
                "[ APOSTATUDO.BET.BR ] Saldo recebido: {variavel} Cashback foi creditado, resgate "
                "em ate 24H\n{variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO.BET.BR ] Saldo recebido: R$2.51 Cashback foi creditado, resgate em ate 24H http://sms.apostatudo.bet.br/l9Ojs1",
                "[ APOSTATUDO.BET.BR ] Saldo recebido: R$16 Cashback foi creditado, resgate em ate 24H http://sms.apostatudo.bet.br/6qOjs1",
                "[ APOSTATUDO.BET.BR ] Saldo recebido: R$2.97 Cashback foi creditado, resgate em ate 24H http://sms.apostatudo.bet.br/T9Ojs1",
            ],
            "datas": [
                {"data": "2025-10-27", "total": 1_606, "entregues": 15, "nao_entregues": 1_591},
                {"data": "2025-10-28", "total": 1_940, "entregues": 1_141, "nao_entregues": 799},
                {"data": "2025-10-29", "total": 2_031, "entregues": 690, "nao_entregues": 1_341},
                {"data": "2025-10-31", "total": 2_110, "entregues": 1_898, "nao_entregues": 212},
            ],
        },
        {
            "id": 16,
            "total": 11,
            "entregues": 3,
            "nao_entregues": 8,
            "texto_base": (
                "[ APOSTATUDO ] ATENCAO!!! Com voce ao nosso lado, podemos vencer o Premio Reclame "
                "AQUI. De seu voto agora Link: {variavel}"
            ),
            "exemplos": [
                "[ APOSTATUDO ] ATENCAO!!! Com voce ao nosso lado, podemos vencer o Premio Reclame AQUI. De seu voto agora Link: http://sms.apostatudo.bet.br/XB36d1",
                "[ APOSTATUDO ] ATENCAO!!! Com voce ao nosso lado, podemos vencer o Premio Reclame AQUI. De seu voto agora Link: http://sms.apostatudo.bet.br/VB36d1",
                "[ APOSTATUDO ] ATENCAO!!! Com voce ao nosso lado, podemos vencer o Premio Reclame AQUI. De seu voto agora Link: http://sms.apostatudo.bet.br/XB36d1",
            ],
            "datas": [
                {"data": "2025-10-29", "total": 11, "entregues": 3, "nao_entregues": 8},
            ],
        },
        {
            "id": 17,
            "total": 7,
            "entregues": 6,
            "nao_entregues": 1,
            "texto_base": (
                "[ APOSTATUDO ] Voce foi selecionado para o Torneio Playtech!!! Sao 100 vencedores "
                "e 25 MIL em premios esta semana!"
            ),
            "exemplos": [
                "[ APOSTATUDO ] Voce foi selecionado para o Torneio Playtech!!! Sao 100 vencedores e 25 MIL em premios esta semana!",
            ],
            "datas": [
                {"data": "2025-10-23", "total": 7, "entregues": 6, "nao_entregues": 1},
            ],
        },
        {
            "id": 18,
            "total": 2,
            "entregues": 2,
            "nao_entregues": 0,
            "texto_base": (
                "APOSTATUDO: Ate 10 GIROS liberados!!! {variavel} estamos te esperandooo! "
                "Clica e saiba como RESGATAR Link: {variavel}"
            ),
            "exemplos": [
                "APOSTATUDO: Ate 10 GIROS liberados!!! Guilherme estamos te esperandooo! Clica e saiba como RESGATAR Link: https://sms.apostatudo.bet.br/LDkkd1",
                "APOSTATUDO: Ate 10 GIROS liberados!!! MARIA estamos te esperandooo! Clica e saiba como RESGATAR Link: https://sms.apostatudo.bet.br/KDkkd1",
            ],
            "datas": [
                {"data": "2025-10-30", "total": 2, "entregues": 2, "nao_entregues": 0},
            ],
        },
    ],
}


# ======================================================================================
# FUNCOES AUXILIARES

def format_number(value: int) -> str:
    """Formata inteiros usando um separador de milhar com ponto."""
    return f"{int(value):,}".replace(",", ".")


def resumo_html(report: Dict[str, object]) -> str:
    """Gera o trecho HTML do resumo principal."""
    mensagens = report["mensagens"]
    datas_html = "\n".join(
        f'      <li><strong>{item["data"]}</strong>: {format_number(item["total"])} mensagens</li>'
        for item in report["datas"]  # type: ignore[index]
    )

    return f"""  <section class="resumo">
    <h1>{report['titulo']}</h1>
    <div class="metricas">
      <div class="metrica">
        <span class="label">Mensagens totais</span>
        <span class="valor">{format_number(mensagens['total'])}</span>
      </div>
      <div class="metrica">
        <span class="label">Entregues</span>
        <span class="valor sucesso">{format_number(mensagens['entregues'])}</span>
      </div>
      <div class="metrica">
        <span class="label">Nao entregues</span>
        <span class="valor alerta">{format_number(mensagens['nao_entregues'])}</span>
      </div>
    </div>
    <h2>Datas com mensagens</h2>
    <ul class="datas">
{datas_html}
    </ul>
  </section>"""


def agrupamento_html(grupo: Dict[str, object]) -> str:
    """Gera o trecho HTML de um agrupamento."""
    metricas = f"""
    <div class="metricas">
      <div class="metrica">
        <span class="label">Total</span>
        <span class="valor">{format_number(grupo['total'])}</span>
      </div>
      <div class="metrica">
        <span class="label">Entregues</span>
        <span class="valor sucesso">{format_number(grupo['entregues'])}</span>
      </div>
      <div class="metrica">
        <span class="label">Nao entregues</span>
        <span class="valor alerta">{format_number(grupo['nao_entregues'])}</span>
      </div>
    </div>"""

    texto_base = "<br/>".join(str(grupo["texto_base"]).strip().splitlines())
    exemplos_html = "\n".join(f"      <li>{exemplo}</li>" for exemplo in grupo["exemplos"])  # type: ignore[index]
    linhas_datas = "\n".join(
        "      <tr>"
        f"<td>{item['data']}</td>"
        f"<td>{format_number(item['total'])}</td>"
        f"<td>{format_number(item['entregues'])}</td>"
        f"<td>{format_number(item['nao_entregues'])}</td>"
        "</tr>"
        for item in grupo["datas"]  # type: ignore[index]
    )

    return f"""  <section class="agrupamento">
    <h2>Agrupamento [{grupo['id']}]</h2>
{metricas}
    <p class="texto-base"><strong>Texto base:</strong><br/>{texto_base}</p>
    <h3>Exemplos de mensagens</h3>
    <ul class="exemplos">
{exemplos_html}
    </ul>
    <h3>Datas</h3>
    <table class="tabela-datas">
      <thead>
        <tr>
          <th>Data</th>
          <th>Total</th>
          <th>Entregues</th>
          <th>Nao entregues</th>
        </tr>
      </thead>
      <tbody>
{linhas_datas}
      </tbody>
    </table>
  </section>"""


def montar_html_completo(report: Dict[str, object]) -> str:
    """Gera um HTML completo com resumo + agrupamentos."""
    partes = [resumo_html(report)]
    partes.extend(agrupamento_html(grupo) for grupo in report["agrupamentos"])  # type: ignore[index]
    corpo = "\n\n".join(partes)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>{report['titulo']}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      color: #212529;
      margin: 32px;
      background-color: #f8f9fa;
    }}
    h1, h2, h3 {{
      color: #1b1f24;
      margin-bottom: 8px;
    }}
    .resumo, .agrupamento {{
      background: #ffffff;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }}
    .metricas {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin: 16px 0;
    }}
    .metrica {{
      flex: 1 1 160px;
      padding: 16px;
      border-radius: 6px;
      border: 1px solid #e9ecef;
      background-color: #f1f3f5;
    }}
    .metrica .label {{
      display: block;
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #6c757d;
    }}
    .metrica .valor {{
      font-size: 20px;
      font-weight: 700;
      margin-top: 6px;
      display: inline-block;
    }}
    .metrica .valor.sucesso {{
      color: #24722a;
    }}
    .metrica .valor.alerta {{
      color: #a61e4d;
    }}
    .datas {{
      list-style: disc;
      padding-left: 20px;
      margin: 8px 0 0;
    }}
    .texto-base {{
      line-height: 1.4;
    }}
    .exemplos {{
      list-style: square;
      padding-left: 20px;
      margin: 8px 0 16px;
    }}
    .tabela-datas {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    .tabela-datas th, .tabela-datas td {{
      border: 1px solid #ced4da;
      padding: 6px 10px;
      text-align: left;
    }}
    .tabela-datas thead {{
      background-color: #e9ecef;
    }}
  </style>
</head>
<body>
{corpo}
</body>
</html>
"""


def salvar_html(report: Dict[str, object], destino: Path) -> None:
    """Salva um HTML completo e, opcionalmente, um arquivo por agrupamento."""
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "relatorio.html").write_text(montar_html_completo(report), encoding="utf-8")

    for grupo in report["agrupamentos"]:  # type: ignore[index]
        html = montar_html_completo(
            {**report, "agrupamentos": [grupo]}
        )  # Reaproveita o mesmo layout com apenas um agrupamento
        nome = f"agrupamento-{grupo['id']:02d}.html"
        (destino / nome).write_text(html, encoding="utf-8")


def montar_estilos() -> StyleSheet1:
    """Cria o conjunto de estilos usados no PDF."""
    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            "ReportTitle",
            parent=estilos["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=12,
            textColor=colors.HexColor("#1b1f24"),
        )
    )

    estilos.add(
        ParagraphStyle(
            "SectionTitle",
            parent=estilos["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#1b1f24"),
        )
    )

    estilos.add(
        ParagraphStyle(
            "Label",
            parent=estilos["BodyText"],
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#495057"),
        )
    )

    estilos.add(
        ParagraphStyle(
            "Body",
            parent=estilos["BodyText"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#212529"),
        )
    )

    return estilos


def tabela_metricas(grupo: Dict[str, object]) -> Table:
    """Cria a tabela de metricas principais de um agrupamento."""
    dados = [
        ["Total", "Entregues", "Nao entregues"],
        [
            format_number(grupo["total"]),
            format_number(grupo["entregues"]),
            format_number(grupo["nao_entregues"]),
        ],
    ]
    tabela = Table(dados, colWidths=[150, 150, 150])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#495057")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, 1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#ced4da")),
            ]
        )
    )
    return tabela


def tabela_datas(itens: Iterable[Dict[str, object]]) -> Table:
    """Cria uma tabela com os totais por data."""
    dados = [["Data", "Total", "Entregues", "Nao entregues"]]
    for item in itens:
        dados.append(
            [
                item["data"],
                format_number(item["total"]),
                format_number(item["entregues"]),
                format_number(item["nao_entregues"]),
            ]
        )

    tabela = Table(dados, colWidths=[110, 80, 100, 110])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#343a40")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tabela


def montar_resumo_pdf(report: Dict[str, object], estilos: StyleSheet1) -> List[object]:
    """Cria a pagina de resumo do PDF."""
    elementos: List[object] = []
    elementos.append(Paragraph(report["titulo"], estilos["ReportTitle"]))

    mensagens = report["mensagens"]
    info = [
        ["Mensagens totais", format_number(mensagens["total"])],
        ["Entregues", format_number(mensagens["entregues"])],
        ["Nao entregues", format_number(mensagens["nao_entregues"])],
    ]
    tabela_info = Table(info, colWidths=[200, 160])
    tabela_info.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e9ecef")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#212529")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
            ]
        )
    )
    elementos.append(tabela_info)
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Datas com mensagens:", estilos["SectionTitle"]))

    dados_datas = [["Data", "Total"]] + [
        [item["data"], format_number(item["total"])] for item in report["datas"]  # type: ignore[index]
    ]
    tabela_datas_resumo = Table(dados_datas, colWidths=[120, 120])
    tabela_datas_resumo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#343a40")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elementos.append(tabela_datas_resumo)
    elementos.append(PageBreak())
    return elementos


def montar_agrupamento_pdf(grupo: Dict[str, object], estilos: StyleSheet1) -> List[object]:
    """Monta a pagina de um agrupamento."""
    elementos: List[object] = []
    elementos.append(Paragraph(f"Agrupamento [{grupo['id']}]", estilos["SectionTitle"]))
    elementos.append(tabela_metricas(grupo))
    elementos.append(Spacer(1, 12))

    texto_base = "<br/>".join(str(grupo["texto_base"]).strip().splitlines())
    elementos.append(Paragraph("<strong>Texto base:</strong>", estilos["Label"]))
    elementos.append(Paragraph(texto_base, estilos["Body"]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Exemplos de mensagens:", estilos["Label"]))
    exemplos_formatados = "<br/>".join(grupo["exemplos"])  # type: ignore[index]
    elementos.append(Paragraph(exemplos_formatados, estilos["Body"]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Datas:", estilos["Label"]))
    elementos.append(tabela_datas(grupo["datas"]))  # type: ignore[arg-type]
    return elementos


def gerar_pdf(report: Dict[str, object], caminho_pdf: Path) -> None:
    """Gera o PDF principal contendo resumo + agrupamentos."""
    estilos = montar_estilos()
    doc = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=48,
        title=report["titulo"],
    )

    elementos: List[object] = []
    elementos.extend(montar_resumo_pdf(report, estilos))

    agrupamentos = report["agrupamentos"]  # type: ignore[assignment]
    for indice, grupo in enumerate(agrupamentos):
        elementos.extend(montar_agrupamento_pdf(grupo, estilos))
        if indice != len(agrupamentos) - 1:
            elementos.append(PageBreak())

    doc.build(elementos)


def parse_args() -> argparse.Namespace:
    """Parseia os parametros de execucao CLI."""
    parser = argparse.ArgumentParser(
        description="Gera PDF e HTML com uma pagina por agrupamento a partir dos dados prontos."
    )
    parser.add_argument(
        "--pdf",
        default="relatorio-agrupamentos.pdf",
        help="Caminho do PDF de saida (padrao: relatorio-agrupamentos.pdf)",
    )
    parser.add_argument(
        "--html-dir",
        default=None,
        help="Se informado, exporta HTML no diretorio especificado.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destino_pdf = Path(args.pdf)
    gerar_pdf(REPORT_DATA, destino_pdf)

    if args.html_dir:
        salvar_html(REPORT_DATA, Path(args.html_dir))

    print(f"PDF gerado em: {destino_pdf}")
    if args.html_dir:
        print(f"HTML exportado para: {Path(args.html_dir).resolve()}")


if __name__ == "__main__":
    main()
