"""Exporta a camada gold para o Tableau.

O Tableau Public lê arquivos (não bancos), então a tabela do dashboard vai para
Excel (.xlsx), que preserva os tipos numéricos independente do idioma do Tableau
(em CSV, o Tableau em português confunde o ponto decimal). Também sai um CSV.
"""
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parents[1]
DB = BASE / "data" / "olist.duckdb"
SAIDA = BASE / "tableau" / "dados"
SAIDA.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB), read_only=True)
for t in ["mart_pedidos_dashboard", "mart_kpis"]:
    df = con.execute(f"SELECT * FROM gold.{t}").df()
    for c in df.select_dtypes("object").columns:  # decimais do DuckDB viram float
        try:
            df[c] = df[c].astype(float)
        except (TypeError, ValueError):
            pass
    df.to_csv(SAIDA / f"{t}.csv", index=False)
    df.to_excel(SAIDA / f"{t}.xlsx", index=False, sheet_name=t[:31])
    print(f"{t}: {len(df):,} linhas -> tableau/dados/{t}.xlsx e .csv")
con.close()
