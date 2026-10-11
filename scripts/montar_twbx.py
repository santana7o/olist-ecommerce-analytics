"""
Monta o dashboard final (tableau/olist_dashboard.twbx) a partir de:
  - tableau/olist_base.twbx  -> criado no Tableau Public conectando o Excel da camada gold
                                (guarda a conexão + extração .hyper, exigida pelo Tableau Public)
  - scripts/gerar_workbook_tableau.py -> planilhas, campos calculados, painéis e navegação
  - tableau/assets/fundo_*.png -> fundos das 3 páginas (estilo cards)

Uso: python scripts/montar_twbx.py
"""
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gerar_workbook_tableau as g  # noqa: E402
import layout_dashboard as L  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
ORIGEM = BASE / "tableau" / "olist_base.twbx"
DESTINO = BASE / "tableau" / "olist_dashboard.twbx"


def main():
    with zipfile.ZipFile(ORIGEM) as z:
        nome_twb = next(n for n in z.namelist() if n.endswith(".twb"))
        twb = z.read(nome_twb).decode("utf-8")
        outros = {n: z.read(n) for n in z.namelist() if n != nome_twb and not n.startswith("Image/")}

    g.DS = re.search(r"<datasource caption='[^']*' inline='true' name='(federated\.[^']+)'", twb).group(1)
    g.SIMPLE_ID = "SheetIdentifierTracking" in twb

    # recursos usados pelo painel (botões de navegação e fundo transparente)
    for recurso in ["BasicButtonObject", "BasicButtonObjectTextSupport", "WorksheetBackgroundTransparency"]:
        if f"<{recurso} />" not in twb:
            twb = twb.replace("  </document-format-change-manifest>", f"    <{recurso} />\n  </document-format-change-manifest>", 1)

    # campos calculados + mapa de cores dentro da fonte de dados
    twb = twb.replace("      <extract ", g.colunas_calculadas() + "\n      <extract ", 1)
    twb = twb.replace("      <semantic-values>", g.estilo_cores_datasource() + "\n      <semantic-values>", 1)
    # troca planilhas / painéis / janelas
    twb = re.sub(r"  <worksheets>.*</windows>", lambda _: g.montar_xml(), twb, flags=re.S)

    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("olist_dashboard.twb", twb)
        for n, dados in outros.items():
            z.writestr(n, dados)
        for p in L.PAGINAS:
            arq = BASE / "tableau" / "assets" / f"fundo_{L.slug(p)}.png"
            z.write(arq, f"Image/{arq.name}")
    print("Dashboard gerado:", DESTINO.relative_to(BASE))


if __name__ == "__main__":
    main()
